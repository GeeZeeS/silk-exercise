// This script initializes the MongoDB database and creates users
db = db.getSiblingDB('admin');

// Create the admin user if not exists
if (db.getUser(process.env.MONGODB_USER) == null) {
  db.createUser({
    user: process.env.MONGODB_USER,
    pwd: process.env.MONGO_PASSWORD,
    roles: [{ role: 'root', db: 'admin' }]
  });
}

// Switch to the application database
db = db.getSiblingDB(process.env.MONGODB_DB);

// Create application database user if not exists
if (db.getUser(process.env.MONGODB_USER) == null) {
  db.createUser({
    user: process.env.MONGODB_USER,
    pwd: process.env.MONGO_PASSWORD,
    roles: [
      { role: 'readWrite', db: process.env.MONGODB_DB },
      { role: 'dbAdmin', db: process.env.MONGODB_DB }
    ]
  });
}

// Create collections if they don't exist
db.createCollection('host_assets');

// Create indexes
db.host_assets.createIndex({ "asset_id": 1 }, { unique: true });
db.host_assets.createIndex({ "address": 1 });
db.host_assets.createIndex({ "name": 1 });
db.host_assets.createIndex({ "os": 1 });
db.host_assets.createIndex({ "cloudProvider": 1 }); 