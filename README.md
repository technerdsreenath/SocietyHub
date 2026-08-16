🚀 Society Hub
A modern, role-based web application designed to streamline housing society management, administration, and resident communication.

📌 Table of Contents
About The Project

Built With

Key Features

Getting Started

Prerequisites

Installation

Usage

Project Structure

Roadmap

Contributing

License

Contact

📖 About The Project
Managing a housing society often involves dealing with fragmented communication, manual maintenance billing, chaotic facility bookings, and unorganized visitor logs. Society Hub solves these challenges by providing a centralized, secure digital portal tailored for apartment complexes and cooperative housing societies.

It features dynamic role-based access control, allowing residents, secretaries, chairpersons, security personnel, and maintenance staff to seamlessly interact within a single unified platform.

🛠 Built With
Backend: Python, Django

Frontend: HTML5, Tailwind CSS (via CDN), Vanilla JavaScript

Icons & UI Assets: Lucide Icons, Google Fonts (Inter)

Database: SQLite (default Django ORM) / PostgreSQL

Version Control: Git & GitHub

✨ Key Features
Role-Based Dynamic Dashboards: Tailored navigation and modules depending on user roles (Resident, Secretary, Chairperson, Security, and Maintenance).

Responsive Mobile Sidebar Drawer: Smooth toggle functionality with outside-click dismissal and full-height alignment for seamless mobile browsing.

Maintenance & Bill Tracking: Residents can view dues, payment statuses, and history, while admins manage financials.

Facility Bookings & Complaints: Effortlessly book shared society amenities and raise or track maintenance complaints.

Dynamic Society Profile Header: Displays building/society names, city details, and custom user role badges directly in the navigation pane.

🚀 Getting Started
Follow these instructions to set up the project locally on your machine for development and testing purposes.

Prerequisites
Make sure you have the following installed on your system:

Git

Python (v3.10 or higher)

Pip (Python Package Manager)

Installation
Clone the repository:

Bash
git clone https://github.com/technerdsreenath/society-hub.git
cd society-hub
Create and activate a virtual environment:

Bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
Install dependencies:

Bash
pip install -r requirements.txt
Set up environment variables:
Create a .env file in the root directory and add your configuration credentials:

Code snippet
DEBUG=True
SECRET_KEY=your_django_secret_key_here
DATABASE_URL=your_database_url_if_using_postgres
Run database migrations:

Bash
python manage.py makemigrations
python manage.py migrate
Run the application:

Bash
python manage.py runserver
Open your browser and navigate to [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

💡 Usage
Once the server is running, log in using your profile credentials. Depending on your assigned role (resident, secretary, chairperson, etc.), the portal will automatically load the appropriate sidebar links, dashboard metrics, and administrative permissions.

📂 Project Structure
Plaintext
society-hub/
│
├── core/                  # Main Django app (models, views, urls)
├── templates/             # HTML templates (base layout, dashboards)
│   └── base.html          # Base layout with responsive sidebar & header
├── static/                # Static assets (CSS, JS, images)
├── manage.py              # Django project management script
├── requirements.txt       # Project dependencies
├── .env.example           # Template for environment variables
└── README.md              # Project documentation
🗺 Roadmap
[x] Initial project setup and database schema design

[x] Responsive layout integration with Tailwind CSS and mobile sidebar drawer

[x] Role-based authentication and modular navigation links

[ ] Bill payment gateway integration

[ ] Automated email/SMS notifications for society notices

🤝 Contributing
Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are greatly appreciated.

Fork the Project

Create your Feature Branch (git checkout -b feature/AmazingFeature)

Commit your Changes (git commit -m 'Add some AmazingFeature')

Push to the Branch (git push origin feature/AmazingFeature)

Open a Pull Request

📜 License
Distributed under the MIT License. See LICENSE for more information.

📬 Contact
Sreenath Shankaran Nair - @technerdsreenath

Project Link: https://github.com/technerdsreenath/society-hub
