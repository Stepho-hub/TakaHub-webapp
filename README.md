# TakaHub

TakaHub is a comprehensive waste management and upcycled product marketplace platform. It enables the collection, categorization, and sale of waste materials, while also allowing artisans to create and sell upcycled products. The platform features an admin approval system for quality control and user identification with role-based display.

## Features

### **Waste Management System**

- Waste sellers (households, businesses, institutions) generate and list recyclable waste materials on the platform.
- Waste items are automatically approved and publicly visible upon listing.
- Workers separate and categorize materials for better organization.
- Buyers (companies or artisans) can purchase waste materials for upcycling.
- Delivery system for waste materials via assigned drivers.

### **Upcycled Product Marketplace**

- Artisans create and sell upcycled products.
- Admin approval required before upcycled products appear in the marketplace.
- Buyers can purchase products and leave ratings/reviews.
- Artisans can view approval status of their products.

### **User Roles & Identification**

- **Admin:** Manages user approvals, product verification, and platform settings. Access to admin dashboard for approving upcycled products.
- **Waste Seller:** Generates and lists recyclable waste materials for sale. Waste items are auto-approved.
- **Driver/Delivery Guy:** Collects and delivers materials. Manages delivery routes and status updates.
- **Artisan/Crafter:** Purchases waste materials and sells upcycled products. Manages product listings with approval status.
- **Buyer:** Purchases waste materials or upcycled products. Can leave reviews and ratings.

### **User Experience Features**

- **User Identification:** Account button displays "Name (Role)" for easy identification (e.g., "Dan (Artisan)")
- **Public Access:** All approved waste and upcycled products visible to logged-in and unlogged users
- **Approval System:** Upcycled products require admin approval; waste items are auto-approved
- **Search & Discovery:** Combined search across waste and upcycled products
- **Role-Based Dashboards:** Tailored interfaces for each user type

## Tech Stack

- **Backend:** Django (Python)
- **Frontend:** HTML, CSS, JavaScript
- **Database:** sqLite
- **Authentication:** Django Auth (with role-based access control)
- **Deployment:** Docker, AWS/Heroku (Planned)

## Installation

1. **Clone the repository**

   ```sh
   git clone https://github.com/Stepho-hub/TakaHub-webapp
   cd TakaHub
   ```

2. **Set up a virtual environment**

   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies**

   ```sh
   pip install -r requirements.txt
   ```

4. **Run database migrations**

   ```sh
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create a superuser (Admin access)**

   ```sh
   python manage.py createsuperuser
   ```

6. **Run the server**
   ```sh
   python manage.py runserver
   ```

## API Endpoints (Planned)

| Endpoint                       | Method | Description                                |
| ------------------------------ | ------ | ------------------------------------------ |
| `/api/waste-items/`            | GET    | List all waste materials                   |
| `/api/waste-items/{id}/`       | GET    | Get details of a specific waste item       |
| `/api/upcycled-products/`      | GET    | List all upcycled products                 |
| `/api/upcycled-products/{id}/` | GET    | Get details of a specific upcycled product |
| `/api/orders/`                 | POST   | Place an order                             |

## Future Enhancements

- Payment gateway integration.
- AI-based waste categorization.
- Mobile app development.

## License

This project is licensed under the [MIT License](LICENSE).

## Contributing

We welcome contributions! If you'd like to contribute:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-name`).
3. Make your changes and commit (`git commit -m 'Add new feature'`).
4. Push to your branch (`git push origin feature-name`).
5. Open a pull request.

## Contact

For any inquiries, feel free to reach out:  
**Author:** Stephen Omwamba
Somtech Technologies  
**📧 Email:** somtechhub@gmail.com

---

Let's turn waste into value! ♻️🚀
