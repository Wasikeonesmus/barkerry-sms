# Upendo Mini Bakery Management System (UM-BMS)

A comprehensive bakery management system built with Django, featuring Mpesa integration for payments.

## Features

- User role management (Admin, Cashier, Baker, Delivery Staff)
- Inventory management with auto-deduction
- Sales management with Mpesa integration
- Order and delivery tracking
- Expense tracking
- Business reports and analytics
- Mobile-first responsive design

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the project root with:
```
DEBUG=True
SECRET_KEY=your-secret-key
MPESA_CONSUMER_KEY=wjvx0E0G6WWGO3PTR0R2GVT7ngSCYRvfied9AH3KdoemEcgC
MPESA_CONSUMER_SECRET=Nmrmh1rBFPgK68qfmguOmFTMmOFg5xwehunQRnjhuTiu6DvTUN9TUA7cjYUtreLL
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

## Technology Stack

- Django 5.2.1
- Bootstrap 5
- SQLite (Development) / PostgreSQL (Production)
- Safaricom Daraja API for Mpesa integration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License. 