from django import forms
from .models import AuditReport

class AuditReportUploadForm(forms.ModelForm):
    class Meta:
        model = AuditReport
        fields = ['title', 'financial_year', 'auditor_name', 'audit_date', 'file', 'remarks']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 bg-portal-bg border border-portal-border rounded-xl text-xs font-semibold text-portal-text focus:outline-none focus:ring-1 focus:ring-portal-primary',
                'placeholder': 'e.g. Statutory Audit Report FY 2025-26',
                'required': True
            }),
            'financial_year': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 bg-portal-bg border border-portal-border rounded-xl text-xs font-semibold text-portal-text focus:outline-none focus:ring-1 focus:ring-portal-primary',
                'placeholder': 'e.g. FY 2025-26'
            }),
            'auditor_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 bg-portal-bg border border-portal-border rounded-xl text-xs font-semibold text-portal-text focus:outline-none focus:ring-1 focus:ring-portal-primary',
                'placeholder': 'e.g. M/s S.K. Agrawal & Co., Chartered Accountants'
            }),
            'audit_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 bg-portal-bg border border-portal-border rounded-xl text-xs font-semibold text-portal-text focus:outline-none focus:ring-1 focus:ring-portal-primary'
            }),
            'file': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 bg-portal-bg border border-portal-border rounded-xl text-xs font-medium text-portal-text focus:outline-none focus:ring-1 focus:ring-portal-primary file:mr-3 file:py-1 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-bold file:bg-portal-primary file:text-white hover:file:bg-portal-primary/90 cursor-pointer',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx',
                'required': True
            }),
            'remarks': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-3 py-2 bg-portal-bg border border-portal-border rounded-xl text-xs font-medium text-portal-text focus:outline-none focus:ring-1 focus:ring-portal-primary',
                'placeholder': 'Key audit observations, auditor opinion (Unqualified/Clean), notes for residents...'
            }),
        }
