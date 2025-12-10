// ============================================================================
// Club Booking System - MongoDB Setup Script
// Phase 2: Database Creation, Collections, Data Insertion, CRUD, Aggregations
// ============================================================================

// Use or create the database
db = db.getSiblingDB("club_booking_db");


// ============================================================================
// 1. DROP EXISTING COLLECTIONS (Optional - for fresh setup)
// ============================================================================
db.membershipLevels.drop();
db.members.drop();
db.facilities.drop();
db.bookings.drop();
db.usageLogs.drop();
db.notifications.drop();

// ============================================================================
// 2. CREATE COLLECTIONS WITH SCHEMA VALIDATION
// ============================================================================

// Create membershipLevels collection with schema validation
db.createCollection("membershipLevels", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["name", "maxBookingsPerDay", "price"],
      properties: {
        _id: { bsonType: "objectId" },
        name: {
          bsonType: "string",
          description: "Membership level name (Basic, Premium, VIP)"
        },
        maxBookingsPerDay: {
          bsonType: "int",
          minimum: 1,
          description: "Maximum bookings allowed per day"
        },
        advanceBookingWindowDays: {
          bsonType: "int",
          minimum: 1,
          description: "Days in advance member can book"
        },
        accessibleFacilityTypes: {
          bsonType: "array",
          items: { bsonType: "string" },
          description: "List of facility types accessible at this level"
        },
        price: {
          bsonType: ["int", "double"],
          minimum: 0,
          description: "Monthly subscription price"
        }
      }
    }
  }
});

// Create members collection with schema validation
db.createCollection("members", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["firstName", "lastName", "email", "phone", "membershipLevelId", "status"],
      properties: {
        _id: { bsonType: "objectId" },
        firstName: {
          bsonType: "string",
          description: "Member first name"
        },
        lastName: {
          bsonType: "string",
          description: "Member last name"
        },
        email: {
          bsonType: "string",
          pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
          description: "Member email address"
        },
        phone: {
          bsonType: ["int", "long"],
          description: "Member phone number"
        },
        membershipLevelId: {
          bsonType: "objectId",
          description: "Reference to membership level"
        },
        status: {
          bsonType: "string",
          enum: ["active", "inactive", "suspended"],
          description: "Member account status"
        },
        activeBookingsCount: {
          bsonType: "int",
          minimum: 0,
          description: "Count of active bookings"
        },
        password: {
          bsonType: "string",
          description: "Member login password (hashed in production)"
        }
      }
    }
  }
});

// Create facilities collection
db.createCollection("facilities", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["name", "type", "status"],
      properties: {
        _id: { bsonType: "objectId" },
        name: {
          bsonType: "string",
          description: "Facility name"
        },
        type: {
          bsonType: "string",
          enum: ["gym", "pool", "court", "studio"],
          description: "Type of facility"
        },
        status: {
          bsonType: "string",
          enum: ["available", "maintenance", "closed"],
          description: "Facility operational status"
        },
        maintenanceNote: {
          bsonType: "string",
          description: "Maintenance or closure notes"
        },
        bookedSlots: {
          bsonType: "array",
          description: "Array of booked time slots"
        },
        assignedStaff: {
          bsonType: "array",
          items: {
            bsonType: "object",
            properties: {
              name: { bsonType: "string" },
              role: { bsonType: "string" },
              contact: { bsonType: "string" }
            }
          },
          description: "Staff assigned to manage facility"
        },
        openingHours: {
          bsonType: "array",
          items: {
            bsonType: "object",
            properties: {
              day: { bsonType: "string" },
              open: { bsonType: "string" },
              close: { bsonType: "string" }
            }
          },
          description: "Operating hours by day"
        }
      }
    }
  }
});

// Create bookings collection
db.createCollection("bookings", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["memberId", "facilityId", "startTime", "status"],
      properties: {
        _id: { bsonType: "objectId" },
        memberId: {
          bsonType: "objectId",
          description: "Reference to member"
        },
        facilityId: {
          bsonType: "objectId",
          description: "Reference to facility"
        },
        startTime: {
          bsonType: "string",
          description: "Booking start time"
        },
        endTime: {
          bsonType: "string",
          description: "Booking end time"
        },
        durationMinutes: {
          bsonType: "int",
          minimum: 15,
          description: "Duration of booking in minutes"
        },
        status: {
          bsonType: "string",
          enum: ["confirmed", "pending", "cancelled", "completed"],
          description: "Booking status"
        },
        payment: {
          bsonType: "object",
          properties: {
            amount: { bsonType: ["int", "double"], minimum: 0 },
            method: { bsonType: "string" },
            status: { bsonType: "string" },
            paidAt: { bsonType: ["string", "null"] }
          },
          description: "Embedded payment information"
        },
        notes: {
          bsonType: "string",
          description: "Additional booking notes"
        }
      }
    }
  }
});

// Create usageLogs collection
db.createCollection("usageLogs");

// Create notifications collection
db.createCollection("notifications");

// ============================================================================
// 3. CREATE INDEXES FOR PERFORMANCE
// ============================================================================

// Index for members by email (search, login)
db.members.createIndex({ "email": 1 }, { unique: true });

// Index for members by status (filter active members)
db.members.createIndex({ "status": 1 });

// Index for bookings by memberId (find member's bookings)
db.bookings.createIndex({ "memberId": 1, "status": 1 });

// Index for bookings by facilityId (find facility bookings)
db.bookings.createIndex({ "facilityId": 1, "status": 1 });

// Index for usageLogs by memberId and checkIn date (time-based queries)
db.usageLogs.createIndex({ "memberId": 1, "checkIn": -1 });

// Index for notifications by memberId (recent notifications)
db.notifications.createIndex({ "memberId": 1, "createdAt": -1 });

// ============================================================================
// 4. INSERT SAMPLE DATA (Minimum 10 documents per collection)
// ============================================================================

// INSERT MEMBERSHIP LEVELS
db.membershipLevels.insertMany([
  {
    _id: ObjectId("691f4f4557dc9a85d45a7993"),
    name: "Basic",
    maxBookingsPerDay: 1,
    advanceBookingWindowDays: 7,
    accessibleFacilityTypes: ["gym"],
    price: 100
  },
  {
    _id: ObjectId("691f4f4557dc9a85d45a7994"),
    name: "Premium",
    maxBookingsPerDay: 3,
    advanceBookingWindowDays: 30,
    accessibleFacilityTypes: ["gym", "pool", "court"],
    price: 300
  },
  {
    _id: ObjectId("691f4f4557dc9a85d45a7a00"),
    name: "VIP",
    maxBookingsPerDay: 5,
    advanceBookingWindowDays: 60,
    accessibleFacilityTypes: ["gym", "pool", "court", "studio"],
    price: 500
  }
]);

// INSERT MEMBERS (13 documents)
db.members.insertMany([
  {
    _id: ObjectId("691f4f4557dc9a85d45a7997"),
    firstName: "Hesham",
    lastName: "El Afandi",
    email: "hesham@example.com",
    phone: 1000000000,
    membershipLevelId: ObjectId("691f4f4557dc9a85d45a7994"),
    status: "active",
    activeBookingsCount: 1,
    password: "default123"
  },
  {
    _id: ObjectId("69206adda94b982d481a230a"),
    firstName: "Mohamed",
    lastName: "Walid",
    email: "mohamedwalid@gmail.com",
    phone: 1001234567,
    membershipLevelId: ObjectId("691f4f4557dc9a85d45a7994"),
    status: "active",
    activeBookingsCount: 1,
    password: "default123"
  },
  {
    _id: ObjectId("691f4f4557dc9a85d45a79a1"),
    firstName: "Fatima",
    lastName: "Hassan",
    email: "fatima@example.com",
    phone: 1001111111,
    membershipLevelId: ObjectId("691f4f4557dc9a85d45a7993"),
    status: "active",
    activeBookingsCount: 0,
    password: "password123"
  },
  {
    _id: ObjectId("691f4f4557dc9a85d45a79a2"),
    firstName: "Ahmed",
    lastName: "Ibrahim",
    email: "ahmed@example.com",
    phone: 1002222222,
    membershipLevelId: ObjectId("691f4f4557dc9a85d45a7a00"),
    status: "active",
    activeBookingsCount: 2,
    password: "secure456"
  },
  {
    _id: ObjectId("691f4f4557dc9a85d45a79a3"),
    firstName: "Layla",
    lastName: "Ahmed",
    email: "layla@example.com",
    phone: 1003333333,
    membershipLevelId: ObjectId("691f4f4557dc9a85d45a7994"),
    status: "active",
    activeBookingsCount: 1,
    password: "pass789"
  },
  {
    _id: ObjectId("691f4f4557dc9a85d45a79a4"),
    firstName: "Ali",
    lastName: "Mohammed",
    email: "ali@example.com",
    phone: 1004444444,
    membershipLevelId: ObjectId("691f4f4557dc9a85d45a7993"),
    status: "inactive",
    activeBookingsCount: 0,
    password: "ali2025"
  },
  {
    _id: ObjectId("691f4f4557dc9a85d45a79a5"),
    firstName: "Noor",
    lastName: "Khalil",
    email: "noor@example.com",
    phone: 1005555555,
    membershipLevelId: ObjectId("691f4f4557dc9a85d45a7a00"),
    status: "active",
    activeBookingsCount: 3,
    password: "noor123"
  },
  {
    _id: ObjectId("691f4f4557dc9a85d45a79a6"),
    firstName: "Sara",
    lastName: "Khalid",
    email: "sara@example.com",
    phone: 1006666666,
    membershipLevelId: ObjectId("691f4f4557dc9a85d45a7994"),
    status: "active",
    activeBookingsCount: 0,
    password: "sara456"
  },
  {
    _id: ObjectId("691f4f4557dc9a85d45a79a7"),
    firstName: "Karim",
    lastName: "Hassan",
    email: "karim@example.com",
    phone: 1007777777,
    membershipLevelId: ObjectId("691f4f4557dc9a85d45a7993"),
    status: "suspended",
    activeBookingsCount: 0,
    password: "karim789"
  },
  {
    _id: ObjectId("691f4f4557dc9a85d45a79a8"),
    firstName: "Mona",
    lastName: "Saleh",
    email: "mona@example.com",
    phone: 1008888888,
    membershipLevelId: ObjectId("691f4f4557dc9a85d45a7a00"),
    status: "active",
    activeBookingsCount: 2,
    password: "mona321"
  },
  {
    _id: ObjectId("691f4f4557dc9a85d45a79a9"),
    firstName: "Omar",
    lastName: "Abbas",
    email: "omar@example.com",
    phone: 1009999999,
    membershipLevelId: ObjectId("691f4f4557dc9a85d45a7994"),
    status: "active",
    activeBookingsCount: 1,
    password: "omar654"
  },
  {
    _id: ObjectId("691f4f4557dc9a85d45a79aa"),
    firstName: "Rania",
    lastName: "Mohsen",
    email: "rania@example.com",
    phone: 1010101010,
    membershipLevelId: ObjectId("691f4f4557dc9a85d45a7993"),
    status: "active",
    activeBookingsCount: 0,
    password: "rania987"
  },
  {
    _id: ObjectId("691f4f4557dc9a85d45a79ab"),
    firstName: "Zain",
    lastName: "Karim",
    email: "zain@example.com",
    phone: 1011111111,
    membershipLevelId: ObjectId("691f4f4557dc9a85d45a7a00"),
    status: "active",
    activeBookingsCount: 1,
    password: "zain111"
  }
]);

// INSERT FACILITIES (10 documents)
db.facilities.insertMany([
  {
    _id: ObjectId("691f4f4557dc9a85d45a7995"),
    name: "Gym A",
    type: "gym",
    status: "available",
    maintenanceNote: "",
    bookedSlots: [],
    assignedStaff: [
      { name: "Ahmed", role: "manager", contact: "010-1234-5678" },
      { name: "Hassan", role: "trainer", contact: "010-9876-5432" }
    ],
    openingHours: [
      { day: "Mon", open: "06:00", close: "22:00" },
      { day: "Tue", open: "06:00", close: "22:00" },
      { day: "Wed", open: "06:00", close: "22:00" },
      { day: "Thu", open: "06:00", close: "22:00" },
      { day: "Fri", open: "07:00", close: "20:00" }
    ]
  },
  {
    _id: ObjectId("691f4f4557dc9a85d45a7996"),
    name: "Pool 1",
    type: "pool",
    status: "available",
    maintenanceNote: "Regular cleaning schedule",
    bookedSlots: [],
    assignedStaff: [
      { name: "Mona", role: "lifeguard", contact: "011-1111-1111" },
      { name: "Samir", role: "manager", contact: "011-2222-2222" }
    ],
    openingHours: [
      { day: "Mon", open: "08:00", close: "20:00" },
      { day: "Tue", open: "08:00", close: "20:00" },
      { day: "Wed", open: "08:00", close: "20:00" },
      { day: "Thu", open: "08:00", close: "20:00" }
    ]
  },
  {
    _id: ObjectId("691f4f4557dc9a85d45a7997"),
    name: "Tennis Court 1",
    type: "court",
    status: "available",
    maintenanceNote: "",
    bookedSlots: [],
    assignedStaff: [
      { name: "Coach Amr", role: "instructor", contact: "012-3333-3333" }
    ],
    openingHours: [
      { day: "Mon", open: "09:00", close: "18:00" },
      { day: "Tue", open: "09:00", close: "18:00" },
      { day: "Wed", open: "09:00", close: "18:00" }
    ]
  },
  {
    _id: ObjectId("691f4f4557dc9a85d45a7998"),
    name: "Yoga Studio",
    type: "studio",
    status: "available",
    maintenanceNote: "",
    bookedSlots: [],
    assignedStaff: [
      { name: "Nada", role: "instructor", contact: "012-4444-4444" }
    ],
    openingHours: [
      { day: "Mon", open: "07:00", close: "19:00" },
      { day: "Tue", open: "07:00", close: "19:00" }
    ]
  },
  {
    _id: ObjectId("691f4f4557dc9a85d45a7999"),
    name: "Gym B",
    type: "gym",
    status: "available",
    maintenanceNote: "",
    bookedSlots: [],
    assignedStaff: [
      { name: "Tariq", role: "manager", contact: "010-5555-5555" }
    ],
    openingHours: [
      { day: "Mon", open: "06:00", close: "21:00" },
      { day: "Tue", open: "06:00", close: "21:00" }
    ]
  },
  {
    _id: ObjectId("691f4f4557dc9a85d45a799a"),
    name: "Basketball Court",
    type: "court",
    status: "maintenance",
    maintenanceNote: "Resurfacing in progress, expected to reopen on Dec 20",
    bookedSlots: [],
    assignedStaff: [],
    openingHours: []
  },
  {
    _id: ObjectId("691f4f4557dc9a85d45a799b"),
    name: "Pool 2",
    type: "pool",
    status: "available",
    maintenanceNote: "Recently upgraded filtration system",
    bookedSlots: [],
    assignedStaff: [
      { name: "Lina", role: "lifeguard", contact: "011-6666-6666" }
    ],
    openingHours: [
      { day: "Wed", open: "09:00", close: "18:00" },
      { day: "Thu", open: "09:00", close: "18:00" }
    ]
  },
  {
    _id: ObjectId("691f4f4557dc9a85d45a799c"),
    name: "Squash Court 1",
    type: "court",
    status: "available",
    maintenanceNote: "",
    bookedSlots: [],
    assignedStaff: [
      { name: "Khaled", role: "instructor", contact: "012-7777-7777" }
    ],
    openingHours: [
      { day: "Mon", open: "10:00", close: "20:00" },
      { day: "Thu", open: "10:00", close: "20:00" }
    ]
  },
  {
    _id: ObjectId("691f4f4557dc9a85d45a799d"),
    name: "CrossFit Studio",
    type: "studio",
    status: "available",
    maintenanceNote: "",
    bookedSlots: [],
    assignedStaff: [
      { name: "Ibrahim", role: "trainer", contact: "012-8888-8888" }
    ],
    openingHours: [
      { day: "Tue", open: "06:00", close: "18:00" },
      { day: "Fri", open: "06:00", close: "18:00" }
    ]
  },
  {
    _id: ObjectId("691f4f4557dc9a85d45a799e"),
    name: "Swimming Pool - Olympic",
    type: "pool",
    status: "available",
    maintenanceNote: "Temperature controlled",
    bookedSlots: [],
    assignedStaff: [
      { name: "Samira", role: "lifeguard", contact: "011-9999-9999" },
      { name: "Coach Mazen", role: "instructor", contact: "011-0000-0000" }
    ],
    openingHours: [
      { day: "Mon", open: "07:00", close: "19:00" },
      { day: "Wed", open: "07:00", close: "19:00" }
    ]
  }
]);

// INSERT BOOKINGS (12 documents)
db.bookings.insertMany([
  {
    _id: ObjectId("692079cddc2b31438b57e0fb"),
    memberId: ObjectId("691f4f4557dc9a85d45a7997"),
    facilityId: ObjectId("691f4f4557dc9a85d45a7995"),
    startTime: "2025-01-15T17:00:00",
    endTime: "2025-01-15T18:00:00",
    durationMinutes: 60,
    status: "confirmed",
    payment: {
      amount: 120.0,
      method: "credit_card",
      status: "paid",
      paidAt: "2025-01-15T16:59:00"
    }
  },
  {
    _id: ObjectId("692079fddc2b31438b57e0fc"),
    memberId: ObjectId("691f4f4557dc9a85d45a7997"),
    facilityId: ObjectId("691f4f4557dc9a85d45a7995"),
    startTime: "2025-01-20T20:15:00",
    endTime: "2025-01-20T22:15:00",
    durationMinutes: 120,
    status: "confirmed",
    payment: {
      amount: 240.0,
      method: "cash",
      status: "paid",
      paidAt: "2025-01-20T20:14:00"
    }
  },
  {
    _id: ObjectId("6921ae959e2b0a44a1e5c652"),
    memberId: ObjectId("69206adda94b982d481a230a"),
    facilityId: ObjectId("691f4f4557dc9a85d45a7995"),
    startTime: "2025-01-22T23:00:00",
    endTime: "2025-01-23T00:00:00",
    durationMinutes: 60,
    status: "confirmed",
    payment: {
      amount: 120.0,
      method: "card",
      status: "paid",
      paidAt: "2025-01-22T22:59:00"
    }
  },
  {
    _id: ObjectId("6921b45ecda42a8e057a6f99"),
    memberId: ObjectId("691f4f4557dc9a85d45a79a2"),
    facilityId: ObjectId("691f4f4557dc9a85d45a7996"),
    startTime: "2025-01-25T20:00:00",
    endTime: "2025-01-25T21:30:00",
    durationMinutes: 90,
    status: "confirmed",
    payment: {
      amount: 150.0,
      method: "cash",
      status: "paid",
      paidAt: "2025-01-25T19:59:00"
    }
  },
  {
    _id: ObjectId("692b327c99a0f6db128c0648"),
    memberId: ObjectId("691f4f4557dc9a85d45a7997"),
    facilityId: ObjectId("691f4f4557dc9a85d45a7995"),
    startTime: "2025-02-01T22:00:00",
    endTime: "2025-02-02T00:00:00",
    durationMinutes: 120,
    status: "cancelled",
    notes: "Cancelled due to member illness"
  },
  {
    _id: ObjectId("692b33987ca7919a14beb9ac"),
    memberId: ObjectId("691f4f4557dc9a85d45a79a5"),
    facilityId: ObjectId("691f4f4557dc9a85d45a7996"),
    startTime: "2025-02-02T22:00:00",
    endTime: "2025-02-03T00:00:00",
    durationMinutes: 120,
    status: "cancelled",
    notes: "Facility maintenance"
  },
  {
    _id: ObjectId("692b3435df8ba239ee01ed13"),
    memberId: ObjectId("691f4f4557dc9a85d45a79a8"),
    facilityId: ObjectId("691f4f4557dc9a85d45a7997"),
    startTime: "2025-02-05T10:00:00",
    endTime: "2025-02-05T11:00:00",
    durationMinutes: 60,
    status: "confirmed",
    payment: {
      amount: 100.0,
      method: "card",
      status: "paid",
      paidAt: "2025-02-05T09:59:00"
    }
  },
  {
    _id: ObjectId("692b344adf8ba239ee01ed14"),
    memberId: ObjectId("691f4f4557dc9a85d45a79a1"),
    facilityId: ObjectId("691f4f4557dc9a85d45a7998"),
    startTime: "2025-02-08T18:00:00",
    endTime: "2025-02-08T19:00:00",
    durationMinutes: 60,
    status: "confirmed",
    payment: {
      amount: 80.0,
      method: "card",
      status: "paid",
      paidAt: "2025-02-08T17:59:00"
    }
  },
  {
    _id: ObjectId("692b344adf8ba239ee01ed15"),
    memberId: ObjectId("691f4f4557dc9a85d45a79aa"),
    facilityId: ObjectId("691f4f4557dc9a85d45a7999"),
    startTime: "2025-02-10T07:00:00",
    endTime: "2025-02-10T08:30:00",
    durationMinutes: 90,
    status: "pending",
    payment: {
      amount: 135.0,
      method: "pending",
      status: "pending",
      paidAt: null
    }
  },
  {
    _id: ObjectId("692b344adf8ba239ee01ed16"),
    memberId: ObjectId("691f4f4557dc9a85d45a79a3"),
    facilityId: ObjectId("691f4f4557dc9a85d45a799b"),
    startTime: "2025-02-12T14:00:00",
    endTime: "2025-02-12T15:00:00",
    durationMinutes: 60,
    status: "confirmed",
    payment: {
      amount: 110.0,
      method: "card",
      status: "paid",
      paidAt: "2025-02-12T13:59:00"
    }
  },
  {
    _id: ObjectId("692b344adf8ba239ee01ed17"),
    memberId: ObjectId("691f4f4557dc9a85d45a79ab"),
    facilityId: ObjectId("691f4f4557dc9a85d45a799c"),
    startTime: "2025-02-15T15:00:00",
    endTime: "2025-02-15T16:00:00",
    durationMinutes: 60,
    status: "confirmed",
    payment: {
      amount: 105.0,
      method: "card",
      status: "paid",
      paidAt: "2025-02-15T14:59:00"
    }
  },
  {
    _id: ObjectId("692b344adf8ba239ee01ed18"),
    memberId: ObjectId("691f4f4557dc9a85d45a79a2"),
    facilityId: ObjectId("691f4f4557dc9a85d45a799e"),
    startTime: "2025-02-18T08:00:00",
    endTime: "2025-02-18T09:00:00",
    durationMinutes: 60,
    status: "completed",
    payment: {
      amount: 120.0,
      method: "card",
      status: "paid",
      paidAt: "2025-02-18T07:59:00"
    }
  }
]);

// INSERT USAGE LOGS (15 documents)
db.usageLogs.insertMany([
  {
    memberId: ObjectId("691f4f4557dc9a85d45a7997"),
    facilityId: ObjectId("691f4f4557dc9a85d45a7995"),
    checkIn: new Date("2025-01-15T17:05:00Z"),
    checkOut: new Date("2025-01-15T17:55:00Z"),
    durationMinutes: 50,
    sessionStatus: "completed"
  },
  {
    memberId: ObjectId("691f4f4557dc9a85d45a7997"),
    facilityId: ObjectId("691f4f4557dc9a85d45a7995"),
    checkIn: new Date("2025-01-20T20:20:00Z"),
    checkOut: new Date("2025-01-20T22:00:00Z"),
    durationMinutes: 100,
    sessionStatus: "completed"
  },
  {
    memberId: ObjectId("69206adda94b982d481a230a"),
    facilityId: ObjectId("691f4f4557dc9a85d45a7995"),
    checkIn: new Date("2025-01-22T23:05:00Z"),
    checkOut: new Date("2025-01-23T00:00:00Z"),
    durationMinutes: 55,
    sessionStatus: "completed"
  },
  {
    memberId: ObjectId("691f4f4557dc9a85d45a79a2"),
    facilityId: ObjectId("691f4f4557dc9a85d45a7996"),
    checkIn: new Date("2025-01-25T20:05:00Z"),
    checkOut: new Date("2025-01-25T21:20:00Z"),
    durationMinutes: 75,
    sessionStatus: "completed"
  },
  {
    memberId: ObjectId("691f4f4557dc9a85d45a79a5"),
    facilityId: ObjectId("691f4f4557dc9a85d45a7995"),
    checkIn: new Date("2025-02-02T06:00:00Z"),
    checkOut: new Date("2025-02-02T07:30:00Z"),
    durationMinutes: 90,
    sessionStatus: "completed"
  },
  {
    memberId: ObjectId("691f4f4557dc9a85d45a79a8"),
    facilityId: ObjectId("691f4f4557dc9a85d45a7997"),
    checkIn: new Date("2025-02-05T10:05:00Z"),
    checkOut: new Date("2025-02-05T10:55:00Z"),
    durationMinutes: 50,
    sessionStatus: "completed"
  },
  {
    memberId: ObjectId("691f4f4557dc9a85d45a79a1"),
    facilityId: ObjectId("691f4f4557dc9a85d45a7998"),
    checkIn: new Date("2025-02-08T18:05:00Z"),
    checkOut: new Date("2025-02-08T18:55:00Z"),
    durationMinutes: 50,
    sessionStatus: "completed"
  },
  {
    memberId: ObjectId("691f4f4557dc9a85d45a79aa"),
    facilityId: ObjectId("691f4f4557dc9a85d45a7999"),
    checkIn: new Date("2025-02-10T07:05:00Z"),
    checkOut: new Date("2025-02-10T08:20:00Z"),
    durationMinutes: 75,
    sessionStatus: "completed"
  },
  {
    memberId: ObjectId("691f4f4557dc9a85d45a79a3"),
    facilityId: ObjectId("691f4f4557dc9a85d45a799b"),
    checkIn: new Date("2025-02-12T14:10:00Z"),
    checkOut: new Date("2025-02-12T14:50:00Z"),
    durationMinutes: 40,
    sessionStatus: "completed"
  },
  {
    memberId: ObjectId("691f4f4557dc9a85d45a79ab"),
    facilityId: ObjectId("691f4f4557dc9a85d45a799c"),
    checkIn: new Date("2025-02-15T15:05:00Z"),
    checkOut: new Date("2025-02-15T15:50:00Z"),
    durationMinutes: 45,
    sessionStatus: "completed"
  },
  {
    memberId: ObjectId("691f4f4557dc9a85d45a79a2"),
    facilityId: ObjectId("691f4f4557dc9a85d45a799e"),
    checkIn: new Date("2025-02-18T08:05:00Z"),
    checkOut: new Date("2025-02-18T08:55:00Z"),
    durationMinutes: 50,
    sessionStatus: "completed"
  },
  {
    memberId: ObjectId("691f4f4557dc9a85d45a7997"),
    facilityId: ObjectId("691f4f4557dc9a85d45a7995"),
    checkIn: new Date("2025-11-29T21:52:54Z"),
    checkOut: new Date("2025-11-29T21:53:34Z"),
    durationMinutes: 1,
    sessionStatus: "completed"
  },
  {
    memberId: ObjectId("691f4f4557dc9a85d45a79a5"),
    facilityId: ObjectId("691f4f4557dc9a85d45a7996"),
    checkIn: new Date("2025-11-30T08:00:00Z"),
    checkOut: new Date("2025-11-30T09:30:00Z"),
    durationMinutes: 90,
    sessionStatus: "completed"
  },
  {
    memberId: ObjectId("691f4f4557dc9a85d45a79a8"),
    facilityId: ObjectId("691f4f4557dc9a85d45a7995"),
    checkIn: new Date("2025-12-01T06:30:00Z"),
    checkOut: new Date("2025-12-01T07:45:00Z"),
    durationMinutes: 75,
    sessionStatus: "completed"
  },
  {
    memberId: ObjectId("691f4f4557dc9a85d45a79aa"),
    facilityId: ObjectId("691f4f4557dc9a85d45a7998"),
    checkIn: new Date("2025-12-02T18:00:00Z"),
    checkOut: new Date("2025-12-02T19:15:00Z"),
    durationMinutes: 75,
    sessionStatus: "completed"
  }
]);

// INSERT NOTIFICATIONS (12 documents)
db.notifications.insertMany([
  {
    memberId: ObjectId("691f4f4557dc9a85d45a7997"),
    message: "Your booking for Gym A on Jan 15 has been confirmed",
    status: "read",
    createdAt: new Date("2025-01-14T16:00:00Z")
  },
  {
    memberId: ObjectId("691f4f4557dc9a85d45a7997"),
    message: "Booking reminder: Gym A tomorrow at 5 PM",
    status: "read",
    createdAt: new Date("2025-01-14T17:00:00Z")
  },
  {
    memberId: ObjectId("69206adda94b982d481a230a"),
    message: "Your booking for Gym A has been confirmed",
    status: "read",
    createdAt: new Date("2025-01-21T10:00:00Z")
  },
  {
    memberId: ObjectId("691f4f4557dc9a85d45a79a2"),
    message: "Welcome to our club! Here's your welcome bonus",
    status: "read",
    createdAt: new Date("2025-01-23T08:00:00Z")
  },
  {
    memberId: ObjectId("691f4f4557dc9a85d45a79a5"),
    message: "Your booking has been updated",
    status: "unread",
    createdAt: new Date("2025-02-01T15:00:00Z")
  },
  {
    memberId: ObjectId("691f4f4557dc9a85d45a79a8"),
    message: "Payment received for your booking",
    status: "unread",
    createdAt: new Date("2025-02-05T11:00:00Z")
  },
  {
    memberId: ObjectId("691f4f4557dc9a85d45a79a1"),
    message: "New yoga class available! Book now",
    status: "unread",
    createdAt: new Date("2025-02-08T12:00:00Z")
  },
  {
    memberId: ObjectId("691f4f4557dc9a85d45a79aa"),
    message: "Your membership will expire in 30 days",
    status: "read",
    createdAt: new Date("2025-02-09T09:00:00Z")
  },
  {
    memberId: ObjectId("691f4f4557dc9a85d45a79a3"),
    message: "Check-in successful at Pool 2",
    status: "read",
    createdAt: new Date("2025-02-12T14:15:00Z")
  },
  {
    memberId: ObjectId("691f4f4557dc9a85d45a79ab"),
    message: "Booking confirmed for Squash Court 1",
    status: "unread",
    createdAt: new Date("2025-02-15T14:30:00Z")
  },
  {
    memberId: ObjectId("691f4f4557dc9a85d45a79a2"),
    message: "Thank you for your visit to Olympic Pool",
    status: "unread",
    createdAt: new Date("2025-02-18T09:00:00Z")
  },
  {
    memberId: ObjectId("691f4f4557dc9a85d45a7997"),
    message: "Your usage stats are ready to view",
    status: "read",
    createdAt: new Date("2025-12-02T10:00:00Z")
  }
]);

print("✓ Database setup completed successfully!");
print("✓ Collections created with schema validation");
print("✓ Indexes created for performance optimization");
print("✓ Sample data inserted:");
print("  - 3 Membership Levels");
print("  - 13 Members");
print("  - 10 Facilities");
print("  - 12 Bookings");
print("  - 15 Usage Logs");
print("  - 12 Notifications");

// ============================================================================
// 5. CRUD OPERATIONS EXAMPLES
// ============================================================================

print("\n========== CRUD OPERATIONS ==========");

// C - CREATE: Already done with insertMany above

// R - READ: Find all active members
print("\n1. READ: All active members:");
db.members.find({ status: "active" }).limit(3).pretty();

// U - UPDATE: Update member's active bookings count
print("\n2. UPDATE: Increment active bookings for Hesham:");
db.members.updateOne(
  { _id: ObjectId("691f4f4557dc9a85d45a7997") },
  { $inc: { activeBookingsCount: 1 } }
);

// D - DELETE: Delete a cancelled booking
print("\n3. DELETE: Remove a cancelled booking:");
db.bookings.deleteOne({ _id: ObjectId("692b327c99a0f6db128c0648") });

print("✓ CRUD operations completed");

// ============================================================================
// 6. AGGREGATION PIPELINE REPORTS (4+ Required)
// ============================================================================

print("\n========== AGGREGATION PIPELINE REPORTS ==========");

// Report 1: Total Bookings Count
print("\n[REPORT 1] Total Bookings Count:");
db.bookings.aggregate([
  {
    $group: {
      _id: null,
      totalBookings: { $sum: 1 }
    }
  }
]).pretty();

// Report 2: Bookings Grouped by Status
print("\n[REPORT 2] Bookings Grouped by Status:");
db.bookings.aggregate([
  {
    $group: {
      _id: "$status",
      count: { $sum: 1 }
    }
  },
  { $sort: { count: -1 } }
]).pretty();

// Report 3: Total Revenue by Payment Method
print("\n[REPORT 3] Total Revenue by Payment Method:");
db.bookings.aggregate([
  { $match: { "payment.status": "paid" } },
  {
    $group: {
      _id: "$payment.method",
      totalRevenue: { $sum: "$payment.amount" },
      bookingCount: { $sum: 1 }
    }
  },
  { $sort: { totalRevenue: -1 } }
]).pretty();

// Report 4: Member Usage Statistics (Last 30 Days)
print("\n[REPORT 4] Member Usage Statistics (Most Active):");
db.usageLogs.aggregate([
  {
    $group: {
      _id: "$memberId",
      totalMinutes: { $sum: "$durationMinutes" },
      sessionCount: { $sum: 1 },
      averageSessionLength: { $avg: "$durationMinutes" }
    }
  },
  { $sort: { totalMinutes: -1 } },
  { $limit: 5 },
  {
    $lookup: {
      from: "members",
      localField: "_id",
      foreignField: "_id",
      as: "memberInfo"
    }
  },
  {
    $project: {
      _id: 0,
      memberId: "$_id",
      memberName: { $arrayElemAt: ["$memberInfo.firstName", 0] },
      totalMinutes: 1,
      sessionCount: 1,
      averageSessionLength: { $round: ["$averageSessionLength", 2] }
    }
  }
]).pretty();

// Report 5: Facility Usage Distribution
print("\n[REPORT 5] Facility Usage Distribution:");
db.usageLogs.aggregate([
  {
    $group: {
      _id: "$facilityId",
      totalVisits: { $sum: 1 },
      totalMinutes: { $sum: "$durationMinutes" }
    }
  },
  { $sort: { totalVisits: -1 } },
  {
    $lookup: {
      from: "facilities",
      localField: "_id",
      foreignField: "_id",
      as: "facilityInfo"
    }
  },
  {
    $project: {
      _id: 0,
      facilityName: { $arrayElemAt: ["$facilityInfo.name", 0] },
      facilityType: { $arrayElemAt: ["$facilityInfo.type", 0] },
      totalVisits: 1,
      totalMinutes: 1,
      averageSessionLength: { $round: [{ $divide: ["$totalMinutes", "$totalVisits"] }, 2] }
    }
  }
]).pretty();

print("\n✓ All aggregation pipelines completed successfully!");

