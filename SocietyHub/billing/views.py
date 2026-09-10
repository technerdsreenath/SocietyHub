import os
import json
try:
    import razorpay
except ImportError:
    razorpay = None

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, FileResponse, Http404
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .models import PaymentTransaction, AuditReport
from .forms import AuditReportUploadForm
from .utils import (
    generate_receipt_pdf, 
    generate_bill_pdf, 
    number_to_words_inr,
    get_or_create_schedule_config,
    execute_auto_dispatch_for_society
)

# Setup Razorpay client with fallback for development/demo
RAZORPAY_KEY_ID = getattr(settings, 'RAZORPAY_KEY_ID', os.getenv('RAZORPAY_KEY_ID', 'rzp_test_societyhub_demo'))
RAZORPAY_KEY_SECRET = getattr(settings, 'RAZORPAY_KEY_SECRET', os.getenv('RAZORPAY_KEY_SECRET', 'test_secret_placeholder'))

def get_razorpay_client():
    if not razorpay:
        return None
    try:
        return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    except Exception:
        return None

@login_required(login_url='login')
def billing_home(request):
    """
    Main billing & payment dues portal for residents and society administration.
    """
    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_approved:
        return render(request, 'auth/pending_approval.html', {'profile': profile})

    # Auto-dispatch evaluation: If scheduled date arrived, automatically dispatch pending bills
    if profile.society and profile.role in ['secretary', 'chairperson']:
        try:
            auto_res = execute_auto_dispatch_for_society(profile.society, force=False)
            if auto_res.get('dispatched'):
                messages.info(request, f"Automatic Dispatch Executed: {auto_res['reason']}")
        except Exception:
            pass

    # If resident, show their transactions; if admin/secretary, show society-wide transactions
    if profile.role in ['secretary', 'chairperson']:
        transactions = PaymentTransaction.objects.filter(society=profile.society).select_related('user')
    else:
        transactions = PaymentTransaction.objects.filter(user=request.user, society=profile.society)

    payment_heads = [c for c in PaymentTransaction.PAYMENT_TYPE_CHOICES if c[0] != 'repair_fund']

    # Summary metrics
    total_paid = sum(t.amount for t in transactions.filter(status='success'))
    pending_count = transactions.filter(status='pending').count()
    success_count = transactions.filter(status='success').count()

    return render(request, 'billing/billing_home.html', {
        'profile': profile,
        'transactions': transactions,
        'payment_heads': payment_heads,
        'total_paid': total_paid,
        'pending_count': pending_count,
        'success_count': success_count,
    })


@login_required(login_url='login')
def initiate_payment_view(request):
    """
    Allows residents to select Maharashtra Model Bye-Law No. 65 payment heads and initiate Razorpay checkout.
    """
    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_approved:
        return render(request, 'auth/pending_approval.html', {'profile': profile})

    payment_heads = [c for c in PaymentTransaction.PAYMENT_TYPE_CHOICES if c[0] != 'repair_fund']

    if request.method == 'POST':
        payment_type = request.POST.get('payment_type')
        amount = request.POST.get('amount')
        remarks = request.POST.get('remarks', '').strip()

        if not payment_type or not amount:
            messages.error(request, "Please select a payment head and enter a valid amount.")
            return redirect('initiate_payment')

        try:
            amount_val = float(amount)
            if amount_val <= 0:
                raise ValueError()
        except ValueError:
            messages.error(request, "Invalid amount entered. Please enter a positive value.")
            return redirect('initiate_payment')

        # Create pending PaymentTransaction record
        transaction = PaymentTransaction.objects.create(
            user=request.user,
            society=profile.society,
            payment_type=payment_type,
            amount=amount_val,
            status='pending',
            remarks=remarks
        )

        amount_in_paise = int(amount_val * 100)
        order_data = {
            'amount': amount_in_paise,
            'currency': 'INR',
            'receipt': f"tx_{transaction.id}",
            'notes': {
                'payment_type': payment_type,
                'society': profile.society.name if profile.society else 'SocietyHub',
                'user_id': request.user.id
            }
        }

        client = get_razorpay_client()
        razorpay_order_id = None
        is_demo_mode = False

        if client and not RAZORPAY_KEY_ID.startswith('rzp_test_societyhub_demo'):
            try:
                razorpay_order = client.order.create(data=order_data)
                razorpay_order_id = razorpay_order.get('id')
            except Exception as e:
                # If Razorpay API credentials are mock or fail, fallback smoothly to demo mode
                is_demo_mode = True
                razorpay_order_id = f"order_demo_{transaction.id}_{int(amount_val)}"
        else:
            is_demo_mode = True
            razorpay_order_id = f"order_demo_{transaction.id}_{int(amount_val)}"

        transaction.razorpay_order_id = razorpay_order_id
        transaction.save()

        return render(request, 'billing/checkout.html', {
            'profile': profile,
            'transaction': transaction,
            'amount_in_paise': amount_in_paise,
            'razorpay_key_id': RAZORPAY_KEY_ID,
            'razorpay_order_id': razorpay_order_id,
            'is_demo_mode': is_demo_mode,
            'head_display': transaction.get_payment_type_display(),
        })

    return render(request, 'billing/initiate_payment.html', {
        'profile': profile,
        'payment_heads': payment_heads,
    })


@csrf_exempt
@login_required(login_url='login')
def payment_callback_view(request):
    """
    Verifies Razorpay payment signature and automatically generates a unique receipt_number upon success.
    """
    if request.method == 'POST':
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        transaction_id = request.POST.get('transaction_id')

        try:
            if transaction_id:
                transaction = PaymentTransaction.objects.get(id=transaction_id, user=request.user)
            elif razorpay_order_id:
                transaction = PaymentTransaction.objects.get(razorpay_order_id=razorpay_order_id, user=request.user)
            else:
                messages.error(request, "Invalid payment callback request.")
                return redirect('billing_home')
        except PaymentTransaction.DoesNotExist:
            messages.error(request, "Payment transaction not found.")
            return redirect('billing_home')

        # Verify signature if live client
        client = get_razorpay_client()
        verified = False

        if client and razorpay_signature and not RAZORPAY_KEY_ID.startswith('rzp_test_societyhub_demo'):
            try:
                params_dict = {
                    'razorpay_order_id': razorpay_order_id,
                    'razorpay_payment_id': razorpay_payment_id,
                    'razorpay_signature': razorpay_signature
                }
                client.utility.verify_payment_signature(params_dict)
                verified = True
            except razorpay.errors.SignatureVerificationError:
                verified = False
        else:
            # Simulated Razorpay Gateway verification
            verified = bool(razorpay_payment_id or razorpay_order_id or transaction)
            if not razorpay_payment_id:
                razorpay_payment_id = f"pay_rzp_{transaction.id}_{int(transaction.amount)}"

        if verified:
            transaction.razorpay_payment_id = razorpay_payment_id
            transaction.razorpay_signature = razorpay_signature or f"sig_rzp_{transaction.id}"
            transaction.status = 'success'
            if not transaction.receipt_number:
                for _ in range(5):
                    try:
                        transaction.receipt_number = PaymentTransaction.generate_receipt_number()
                        transaction.save()
                        break
                    except Exception:
                        transaction.receipt_number = None
            else:
                transaction.save()

            messages.success(request, f"Payment of ₹{transaction.amount:,.2f} completed successfully! Receipt #{transaction.receipt_number} generated.")
            return redirect('view_receipt', pk=transaction.id)
        else:
            transaction.status = 'failed'
            transaction.save()
            messages.error(request, "Payment verification failed. Please try again or contact society administration.")
            return redirect('billing_home')

    return redirect('billing_home')


@login_required(login_url='login')
def download_receipt_pdf_view(request, pk):
    """
    Creates and streams a clean, printable Maharashtra Model Bye-Law No. 65 compliant 
    PDF receipt for download with Society Watermark.
    """
    transaction = get_object_or_404(PaymentTransaction, pk=pk)
    profile = getattr(request.user, 'profile', None)

    # Strictly restricted to the concerned user (the resident who made the payment)
    if transaction.user != request.user and not request.user.is_superuser:
        raise Http404("You do not have permission to access this receipt. Only the concerned paying resident can download the receipt.")

    if transaction.status != 'success':
        messages.warning(request, "Receipt is only available for successful payments.")
        return redirect('billing_home')

    pdf_buffer = generate_receipt_pdf(transaction)
    filename = f"Receipt_{transaction.receipt_number or transaction.id}.pdf"
    
    return FileResponse(
        pdf_buffer,
        as_attachment=True,
        filename=filename,
        content_type='application/pdf'
    )


@login_required(login_url='login')
def download_bill_pdf_view(request, pk):
    """
    Creates and streams an authentic Maharashtra CHS Maintenance Bill PDF with Society Watermark.
    """
    transaction = get_object_or_404(PaymentTransaction, pk=pk)
    profile = getattr(request.user, 'profile', None)

    is_owner = transaction.user == request.user
    is_admin = profile and profile.role in ['secretary', 'chairperson'] and profile.society == transaction.society

    if not (is_owner or is_admin):
        raise Http404("You do not have permission to access this bill.")

    pdf_buffer = generate_bill_pdf(transaction)
    filename = f"Maintenance_Bill_{transaction.bill_number or transaction.id}.pdf"
    
    return FileResponse(
        pdf_buffer,
        as_attachment=True,
        filename=filename,
        content_type='application/pdf'
    )


@login_required(login_url='login')
def view_bill_view(request, pk):
    """
    Printable in-browser HTML view of the Maharashtra CHS Maintenance Bill with Society Watermark.
    """
    transaction = get_object_or_404(PaymentTransaction, pk=pk)
    profile = getattr(request.user, 'profile', None)

    is_owner = transaction.user == request.user
    is_admin = profile and profile.role in ['secretary', 'chairperson'] and profile.society == transaction.society

    if not (is_owner or is_admin):
        raise Http404("You do not have permission to view this bill.")

    words = number_to_words_inr(transaction.amount)
    breakdown = transaction.get_breakdown()

    return render(request, 'billing/bill_detail.html', {
        'transaction': transaction,
        'profile': profile,
        'payer_profile': getattr(transaction.user, 'profile', None),
        'breakdown': breakdown,
        'amount_in_words': words,
    })


@login_required(login_url='login')
def view_receipt_view(request, pk):
    """
    Printable in-browser HTML view of the Maharashtra Model Bye-Law No. 65 payment receipt.
    """
    transaction = get_object_or_404(PaymentTransaction, pk=pk)
    profile = getattr(request.user, 'profile', None)

    # Strictly restricted to the concerned user (the resident who made the payment)
    if transaction.user != request.user and not request.user.is_superuser:
        raise Http404("You do not have permission to view this receipt. Only the concerned paying resident can view the receipt.")

    words = number_to_words_inr(transaction.amount)
    breakdown = transaction.get_breakdown()

    return render(request, 'billing/receipt.html', {
        'transaction': transaction,
        'profile': profile,
        'payer_profile': getattr(transaction.user, 'profile', None),
        'breakdown': breakdown,
        'amount_in_words': words,
    })


@login_required(login_url='login')
def pay_bill_view(request, pk):
    """
    Direct checkout route for a specific pending PaymentTransaction.
    """
    transaction = get_object_or_404(PaymentTransaction, pk=pk)
    profile = getattr(request.user, 'profile', None)

    if not profile or not profile.is_approved:
        return render(request, 'auth/pending_approval.html', {'profile': profile})

    # Strictly ensure that only the respective resident can pay their own bill
    if transaction.user != request.user:
        messages.error(request, "Only the respective resident can pay this maintenance bill.")
        return redirect('billing_home')

    if transaction.status == 'success':
        messages.info(request, f"This bill (#{transaction.receipt_number or transaction.id}) has already been paid.")
        return redirect('view_receipt', pk=transaction.id)

    amount_in_paise = int(transaction.amount * 100)
    order_data = {
        'amount': amount_in_paise,
        'currency': 'INR',
        'receipt': f"tx_{transaction.id}",
        'notes': {
            'payment_type': transaction.payment_type,
            'society': profile.society.name if profile.society else 'SocietyHub',
            'user_id': transaction.user.id
        }
    }

    client = get_razorpay_client()
    razorpay_order_id = transaction.razorpay_order_id
    is_demo_mode = False

    if not razorpay_order_id:
        if client and not RAZORPAY_KEY_ID.startswith('rzp_test_societyhub_demo'):
            try:
                razorpay_order = client.order.create(data=order_data)
                razorpay_order_id = razorpay_order.get('id')
            except Exception:
                is_demo_mode = True
                razorpay_order_id = f"order_demo_{transaction.id}_{int(transaction.amount)}"
        else:
            is_demo_mode = True
            razorpay_order_id = f"order_demo_{transaction.id}_{int(transaction.amount)}"

        transaction.razorpay_order_id = razorpay_order_id
        transaction.save()
    else:
        if RAZORPAY_KEY_ID.startswith('rzp_test_societyhub_demo') or 'demo' in str(razorpay_order_id):
            is_demo_mode = True

    return render(request, 'billing/checkout.html', {
        'profile': profile,
        'transaction': transaction,
        'amount_in_paise': amount_in_paise,
        'razorpay_key_id': RAZORPAY_KEY_ID,
        'razorpay_order_id': razorpay_order_id,
        'is_demo_mode': is_demo_mode,
        'head_display': transaction.get_payment_type_display(),
    })


@login_required(login_url='login')
def set_maintenance_view(request):
    """
    Allows Secretary and Chairperson to configure and generate authentic itemized 
    CHS maintenance bills based on flat area (sq. ft.), flat names, and statutory heads.
    Strictly excludes maintenance staff and security guards.
    """
    import datetime
    from decimal import Decimal
    from SocietyHub.users.models import UserProfile

    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_approved:
        return render(request, 'auth/pending_approval.html', {'profile': profile})

    if profile.role not in ['secretary', 'chairperson']:
        messages.error(request, "Access restricted. Only Secretary and Chairperson can set society maintenance.")
        return redirect('portal_dashboard')

    eligible_profiles = UserProfile.objects.filter(
        society=profile.society,
        is_approved=True,
        role__in=['resident', 'secretary', 'chairperson']
    ).select_related('user').order_by('wing', 'flat_number', 'user__first_name')

    schedule_config = get_or_create_schedule_config(profile.society)

    if request.method == 'POST':
        action = request.POST.get('action', 'generate_bills')

        # 1. Action: Save Automatic Recurring Billing Schedule
        if action == 'save_schedule':
            try:
                schedule_config.is_auto_dispatch_active = (request.POST.get('is_auto_dispatch_active') == 'on')
                schedule_config.dispatch_day = max(1, min(28, int(request.POST.get('dispatch_day', 1))))
                schedule_config.frequency = request.POST.get('frequency', 'monthly')
                schedule_config.due_days = max(1, int(request.POST.get('due_days', 15)))

                # Parse rates from POST
                def parse_rate(k, def_v):
                    try:
                        v = request.POST.get(k, def_v).strip()
                        return Decimal(v) if v else Decimal(def_v)
                    except Exception:
                        return Decimal(def_v)

                schedule_config.prop_tax_rate = parse_rate('prop_tax_rate', str(schedule_config.prop_tax_rate or '5.026'))
                schedule_config.prop_tax_fixed = parse_rate('prop_tax_fixed', str(schedule_config.prop_tax_fixed or '0.00'))
                schedule_config.sinking_rate = parse_rate('sinking_rate', str(schedule_config.sinking_rate or '1.569'))
                schedule_config.sinking_fixed = parse_rate('sinking_fixed', str(schedule_config.sinking_fixed or '0.00'))
                schedule_config.repair_rate = parse_rate('repair_rate', str(schedule_config.repair_rate or '3.147'))
                schedule_config.repair_fixed = parse_rate('repair_fixed', str(schedule_config.repair_fixed or '0.00'))
                schedule_config.service_fixed = parse_rate('service_fixed', str(schedule_config.service_fixed or '3600.00'))
                schedule_config.electricity_fixed = parse_rate('electricity_fixed', str(schedule_config.electricity_fixed or '1350.00'))
                schedule_config.water_fixed = parse_rate('water_fixed', str(schedule_config.water_fixed or '450.00'))
                schedule_config.security_fixed = parse_rate('security_fixed', str(schedule_config.security_fixed or '2100.00'))
                schedule_config.parking_fixed = parse_rate('parking_fixed', str(schedule_config.parking_fixed or '0.00'))
                schedule_config.non_occupancy_fixed = parse_rate('non_occupancy_fixed', str(schedule_config.non_occupancy_fixed or '0.00'))
                schedule_config.save()

                next_d = schedule_config.get_next_dispatch_date()
                messages.success(
                    request, 
                    f"Automatic maintenance billing schedule updated! Next automated dispatch: {next_d:%B %d, %Y} (Day {schedule_config.dispatch_day} of every cycle)."
                )
            except Exception as e:
                messages.error(request, f"Failed to save schedule settings: {e}")
            return redirect('set_maintenance')

        # 2. Action: Immediate Trigger Scheduled Dispatch (Strictly for this society only)
        elif action == 'trigger_auto_dispatch':
            res = execute_auto_dispatch_for_society(profile.society, force=True)
            if res.get('dispatched'):
                messages.success(request, f"Scheduled Auto-Dispatch Run Succeeded for {profile.society.name}: {res['reason']}")
            else:
                messages.warning(request, f"Auto-Dispatch Status: {res.get('reason')}")
            return redirect('billing_home')

        # 3. Action: Manual Batch Bill Generation for Selected Residents (Strictly for this society only)
        billing_period = request.POST.get('billing_period', 'July/August/September 2026').strip()
        bill_date_val = request.POST.get('bill_date')
        due_date_val = request.POST.get('due_date')

        try:
            bill_date = datetime.datetime.strptime(bill_date_val, '%Y-%m-%d').date() if bill_date_val else datetime.date.today()
        except Exception:
            bill_date = datetime.date.today()

        try:
            due_date = datetime.datetime.strptime(due_date_val, '%Y-%m-%d').date() if due_date_val else (bill_date + datetime.timedelta(days=60))
        except Exception:
            due_date = bill_date + datetime.timedelta(days=60)

        # Parse itemized statutory rates from society's own schedule_config
        def parse_dec(key, default='0'):
            try:
                v = request.POST.get(key, default).strip()
                return Decimal(v) if v else Decimal(default)
            except Exception:
                return Decimal(default)

        # Rates & Fixed heads (Defaulted to this specific society's configured rates)
        prop_tax_rate = parse_dec('prop_tax_rate', str(schedule_config.prop_tax_rate or '5.026'))
        prop_tax_fixed = parse_dec('prop_tax_fixed', str(schedule_config.prop_tax_fixed or '0.00'))

        sinking_rate = parse_dec('sinking_rate', str(schedule_config.sinking_rate or '1.569'))
        sinking_fixed = parse_dec('sinking_fixed', str(schedule_config.sinking_fixed or '0.00'))

        repair_rate = parse_dec('repair_rate', str(schedule_config.repair_rate or '3.147'))
        repair_fixed = parse_dec('repair_fixed', str(schedule_config.repair_fixed or '0.00'))

        service_rate = parse_dec('service_rate', str(schedule_config.service_rate or '0.00'))
        service_fixed = parse_dec('service_fixed', str(schedule_config.service_fixed or '3600.00'))

        electricity_fixed = parse_dec('electricity_fixed', str(schedule_config.electricity_fixed or '1350.00'))
        water_fixed = parse_dec('water_fixed', str(schedule_config.water_fixed or '450.00'))
        security_fixed = parse_dec('security_fixed', str(schedule_config.security_fixed or '2100.00'))
        parking_fixed = parse_dec('parking_fixed', str(schedule_config.parking_fixed or '0.00'))
        non_occupancy_fixed = parse_dec('non_occupancy_fixed', str(schedule_config.non_occupancy_fixed or '0.00'))

        selected_user_ids = request.POST.getlist('selected_users')
        if not selected_user_ids:
            messages.error(request, f"Please select at least one resident/flat in {profile.society.name} to generate maintenance bills.")
            return redirect('set_maintenance')

        created_count = 0
        total_amount = Decimal('0')

        # Sequential bill numbering per society
        last_bill_seq = 28
        try:
            last_b = PaymentTransaction.objects.filter(society=profile.society).exclude(bill_number__isnull=True).exclude(bill_number='').order_by('-id').first()
            if last_b and last_b.bill_number:
                last_bill_seq = int(''.join(filter(str.isdigit, str(last_b.bill_number))))
        except Exception:
            last_bill_seq = 28

        for u_id in selected_user_ids:
            try:
                # STRICT check: Resident must belong to THIS society only
                user_prof = eligible_profiles.get(user_id=u_id, society=profile.society)
            except UserProfile.DoesNotExist:
                continue

            # Update flat details if changed
            updated_area = request.POST.get(f"area_{u_id}", '').strip()
            updated_flat_name = request.POST.get(f"flat_name_{u_id}", '').strip()
            profile_changed = False

            if updated_area:
                try:
                    user_prof.area_sqft = Decimal(updated_area)
                    profile_changed = True
                except Exception:
                    pass
            if updated_flat_name and updated_flat_name != user_prof.flat_name:
                user_prof.flat_name = updated_flat_name
                profile_changed = True

            if profile_changed:
                user_prof.save()

            sqft = user_prof.area_sqft or Decimal('850')

            # Calculate itemized particulars for this flat
            prop_tax_amt = (sqft * prop_tax_rate) + prop_tax_fixed if (prop_tax_rate or prop_tax_fixed) else Decimal('0')
            sinking_amt = (sqft * sinking_rate) + sinking_fixed if (sinking_rate or sinking_fixed) else Decimal('0')
            repair_amt = (sqft * repair_rate) + repair_fixed if (repair_rate or repair_fixed) else Decimal('0')
            service_amt = (sqft * service_rate) + service_fixed if (service_rate or service_fixed) else Decimal('0')

            particulars_list = []
            if prop_tax_amt > 0:
                particulars_list.append({"particular": "PROPERTY TAXES", "amount": float(prop_tax_amt)})
            if sinking_amt > 0:
                particulars_list.append({"particular": "SINKING FUND", "amount": float(sinking_amt)})
            if repair_amt > 0:
                particulars_list.append({"particular": "REPAIR FUND", "amount": float(repair_amt)})
            if electricity_fixed > 0:
                particulars_list.append({"particular": "ELECTRICITY CHARGES", "amount": float(electricity_fixed)})
            if water_fixed > 0:
                particulars_list.append({"particular": "WATER CHARGES", "amount": float(water_fixed)})
            if service_amt > 0:
                particulars_list.append({"particular": "SERVICE CHARGES", "amount": float(service_amt)})
            if security_fixed > 0:
                particulars_list.append({"particular": "SECURITY CHARGES", "amount": float(security_fixed)})
            if parking_fixed > 0:
                particulars_list.append({"particular": "PARKING CHARGES", "amount": float(parking_fixed)})
            if non_occupancy_fixed > 0:
                particulars_list.append({"particular": "NON-OCCUPANCY CHARGES", "amount": float(non_occupancy_fixed)})

            subtotal = sum(Decimal(str(item['amount'])) for item in particulars_list)

            # Check for custom manual total override
            custom_total = request.POST.get(f"amount_{u_id}", '').strip()
            if custom_total:
                try:
                    subtotal = Decimal(custom_total)
                except Exception:
                    pass

            # Arrears and interest
            arrears_input = request.POST.get(f"arrears_{u_id}", '0').strip()
            try:
                arrears = Decimal(arrears_input) if arrears_input else Decimal('0')
            except Exception:
                arrears = Decimal('0')

            interest_input = request.POST.get(f"interest_{u_id}", '0').strip()
            try:
                interest = Decimal(interest_input) if interest_input else (arrears * Decimal('0.21') if arrears > 0 else Decimal('0'))
            except Exception:
                interest = Decimal('0')

            grand_total = subtotal + arrears + interest

            if grand_total <= Decimal('0'):
                continue

            last_bill_seq += 1
            bill_no_str = str(last_bill_seq)

            desc_parts = [f"Maintenance Bill ({billing_period})"]
            if user_prof.flat_name:
                desc_parts.append(f"Flat: {user_prof.flat_name}")
            elif user_prof.wing or user_prof.flat_number:
                desc_parts.append(f"Flat: {user_prof.wing or ''}-{user_prof.flat_number or ''}")
            desc_parts.append(f"({user_prof.area_sqft or 850} sq.ft)")

            PaymentTransaction.objects.create(
                user=user_prof.user,
                society=profile.society,
                payment_type='maintenance',
                amount=grand_total,
                subtotal_amount=subtotal,
                arrears_amount=arrears,
                interest_amount=interest,
                bill_number=bill_no_str,
                bill_date=bill_date,
                due_date=due_date,
                billing_period=billing_period,
                breakdown_json=json.dumps(particulars_list),
                status='pending',
                remarks=" | ".join(desc_parts)
            )
            created_count += 1
            total_amount += grand_total

        messages.success(
            request,
            f"Successfully generated and dispatched {created_count} maintenance bills totaling ₹{total_amount:,.2f} for {profile.society.name}."
        )
        return redirect('billing_home')

    return render(request, 'billing/set_maintenance.html', {
        'profile': profile,
        'eligible_profiles': eligible_profiles,
        'total_residents': eligible_profiles.count(),
        'schedule_config': schedule_config,
        'next_dispatch_date': schedule_config.get_next_dispatch_date(),
        'current_period_label': schedule_config.get_current_period_label(),
    })


@login_required(login_url='login')
def delete_bill_view(request, pk):
    """
    Allows Secretary or Chairperson to delete a generated maintenance bill.
    """
    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_approved:
        return render(request, 'auth/pending_approval.html', {'profile': profile})

    if profile.role not in ['secretary', 'chairperson'] and not request.user.is_superuser:
        messages.error(request, "Permission denied. Only Secretary or Chairperson can delete bills.")
        return redirect('billing_home')

    transaction = PaymentTransaction.objects.filter(id=pk).first()
    if not transaction:
        messages.info(request, "This bill has already been removed or does not exist.")
        return redirect('billing_home')

    if profile.society and transaction.society and profile.society != transaction.society and not request.user.is_superuser:
        messages.error(request, "Permission denied. You can only delete bills for your society.")
        return redirect('billing_home')

    if request.method == 'POST':
        bill_ref = transaction.bill_number or f"TXN-{transaction.id}"
        resident_name = transaction.user.get_full_name() or transaction.user.username
        transaction.delete()
        messages.success(request, f"Successfully deleted Maintenance Bill #{bill_ref} for {resident_name}.")

    return redirect('billing_home')


@login_required(login_url='login')
def delete_bulk_bills_view(request):
    """
    Allows Secretary or Chairperson to bulk delete selected or all pending bills.
    """
    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_approved:
        return render(request, 'auth/pending_approval.html', {'profile': profile})

    if profile.role not in ['secretary', 'chairperson'] and not request.user.is_superuser:
        messages.error(request, "Permission denied. Only Secretary or Chairperson can delete bills.")
        return redirect('billing_home')

    if request.method == 'POST':
        action_type = request.POST.get('action_type')
        selected_ids = request.POST.getlist('selected_bills')

        qs = PaymentTransaction.objects.all()
        if profile.society and not request.user.is_superuser:
            qs = qs.filter(society=profile.society)

        if action_type == 'delete_all_pending':
            count, _ = qs.filter(status='pending').delete()
            messages.success(request, f"Successfully deleted all {count} pending maintenance bills.")
        elif selected_ids:
            count, _ = qs.filter(id__in=selected_ids).delete()
            messages.success(request, f"Successfully deleted {count} selected maintenance bill(s).")
        else:
            messages.warning(request, "No bills were selected for deletion.")

    return redirect('billing_home')


@login_required(login_url='login')
def audit_reports_list_view(request):
    """
    Dedicated Society Financial & Statutory Audit Reports section.
    Accessible to all approved residents, secretaries, and chairpersons of the society
    to browse, search, and download official audit reports with society isolation.
    """
    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_approved:
        return render(request, 'auth/pending_approval.html', {'profile': profile})

    # Strictly filter audit reports for the user's society
    reports = AuditReport.objects.filter(society=profile.society)

    # Optional search query (title, auditor, financial year)
    search_query = request.GET.get('q', '').strip()
    if search_query:
        from django.db.models import Q
        reports = reports.filter(
            Q(title__icontains=search_query) |
            Q(financial_year__icontains=search_query) |
            Q(auditor_name__icontains=search_query) |
            Q(remarks__icontains=search_query)
        )

    reports = reports.order_by('-audit_date', '-created_at')

    upload_form = AuditReportUploadForm() if profile.role == 'chairperson' or request.user.is_superuser else None

    # Compute summary stats
    total_audits = reports.count()
    latest_report = reports.first()

    return render(request, 'billing/audit_reports_list.html', {
        'profile': profile,
        'reports': reports,
        'total_audits': total_audits,
        'latest_report': latest_report,
        'search_query': search_query,
        'upload_form': upload_form,
        'is_chairperson': profile.role == 'chairperson' or request.user.is_superuser,
    })


@login_required(login_url='login')
def upload_audit_report_view(request):
    """
    Upload official society audit reports. Strictly restricted to the Chairperson of the society.
    """
    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_approved:
        return render(request, 'auth/pending_approval.html', {'profile': profile})

    if profile.role != 'chairperson' and not request.user.is_superuser:
        messages.error(request, "Access restricted. Only the Society Chairperson can upload official audit reports.")
        return redirect('audit_reports_list')

    if request.method == 'POST':
        form = AuditReportUploadForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.society = profile.society
            report.uploaded_by = request.user
            report.save()
            messages.success(
                request,
                f"Successfully uploaded Audit Report '{report.title}' for {profile.society.name}. It is now available for all society members."
            )
        else:
            errors_str = " ".join([f"{f}: {e[0]}" for f, e in form.errors.items()])
            messages.error(request, f"Failed to upload audit report: {errors_str}")

    redirect_target = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'audit_reports_list'
    return redirect(redirect_target)


@login_required(login_url='login')
def delete_audit_report_view(request, pk):
    """
    Delete an audit report. Strictly restricted to the Society Chairperson.
    """
    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_approved:
        return render(request, 'auth/pending_approval.html', {'profile': profile})

    if profile.role != 'chairperson' and not request.user.is_superuser:
        messages.error(request, "Permission denied. Only the Society Chairperson can remove audit reports.")
        return redirect('audit_reports_list')

    report = get_object_or_404(AuditReport, pk=pk)
    if report.society != profile.society and not request.user.is_superuser:
        messages.error(request, "Permission denied. You can only manage audit reports for your society.")
        return redirect('audit_reports_list')

    if request.method == 'POST':
        report_title = report.title
        # Delete file from disk if present
        if report.file:
            try:
                report.file.delete(save=False)
            except Exception:
                pass
        report.delete()
        messages.success(request, f"Successfully removed Audit Report '{report_title}'.")

    redirect_target = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'audit_reports_list'
    return redirect(redirect_target)


@login_required(login_url='login')
def download_audit_report_view(request, pk):
    """
    Securely download an official Society Audit Report.
    Strictly verifies that the requesting user belongs to the same society as the report.
    """
    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_approved:
        raise Http404("You do not have permission to download this audit report.")

    report = get_object_or_404(AuditReport, pk=pk)

    # Society isolation check
    if report.society != profile.society and not request.user.is_superuser:
        raise Http404("You do not have permission to download audit reports belonging to another society.")

    if not report.file:
        raise Http404("Audit report file not found on the server.")

    try:
        response = FileResponse(report.file.open('rb'), as_attachment=True, filename=report.file.name.split('/')[-1])
        return response
    except Exception as e:
        raise Http404(f"Could not read audit file: {e}")

