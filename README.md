# Club-booking-system

A desktop application for managing bookings, facilities, usage logs, and notifications for a sports club.  
Built using Python (PyQt5) and MongoDB.

---

## Overview

This system provides two separate interfaces:

### Admin Interface
- Full CRUD operations on all collections
- Smart insert dialogs (with dropdowns for referenced fields)
- Embedded payment object support
- Search functionality
- Table-based display for all documents
- Update and delete operations
- Logout feature

### Client Interface
- Member login and logout
- Create and cancel bookings
- Check-in / Check-out with automatic usage logging
- Notifications system
- Booking statistics (aggregation pipelines)
- Usage trends for the last 30 days
- Spending per facility
- Side menu navigation between pages

---

## MongoDB Collections

- members
- membershipLevels
- facilities
- bookings
- usageLogs
- notifications

Embedded documents:
- bookings.payment

---

## Features

### Admin Features
- Insert, edit, delete, search
- Modern UI layout
- Handles embedded documents
- Reference fields shown with dropdowns
- Full CRUD for all collections

### Client Features
- Login/logout
- Create bookings (with payment info)
- Cancel bookings
- Check-in / Check-out
- Notifications viewer with mark-as-read
- Statistics dashboard using aggregation pipelines
- Usage trends table
- Spending per facility table

---

## Aggregation Pipelines Used

1. Total bookings count
2. Bookings grouped by status
3. Total spent (sum of payment amounts)
4. Most used facility
5. Usage minutes per day (last 30 days)
6. Spending per facility

These power the client’s Stats, Usage, and Spending pages.

---

## Running the Project

### 1. Clone the repository
git clone https://github.com/
<your-username>/Club-booking-system.git
cd Club-booking-system

### 2. Create virtual environment
python -m venv venv

### 3. Activate environment (Windows)
venv\Scripts\activate

### 4. Install dependencies
pip install -r requirements.txt

### 5. Set MongoDB URI
Create a `.env` file:
MONGO_URI=mongodb://localhost:27017


### 6. Run the application
python main.py

---

## Sharing the Database

A `Database Collections JSON` folder is created with exported JSON files for all collections.  
Teammates can import them using MongoDB Compass.

---

## Phase 2 Coverage

- CRUD operations implemented
- MongoDB collections and embedded documents
- Aggregation pipelines implemented
- PyQt5 UI (admin + client)
- Notifications system
- Usage logging
- Booking management
- Integrated MongoDB backend
