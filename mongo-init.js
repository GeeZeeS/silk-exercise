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
db.createCollection('integrated_hosts');

// Create indexes for host_assets collection
db.host_assets.createIndex({ "asset_id": 1 }, { unique: true });
db.host_assets.createIndex({ "address": 1 });
db.host_assets.createIndex({ "name": 1 });
db.host_assets.createIndex({ "os": 1 });
db.host_assets.createIndex({ "cloudProvider": 1 });

// Create indexes for integrated_hosts collection
db.integrated_hosts.createIndex({ "qualys_asset_id": 1 });
db.integrated_hosts.createIndex({ "crowdstrike_device_id": 1 });
db.integrated_hosts.createIndex({ "hostname": 1 });
db.integrated_hosts.createIndex({ "primary_ip": 1 });
db.integrated_hosts.createIndex({ "os": 1 });
db.integrated_hosts.createIndex({ "cloud_provider": 1 });
db.integrated_hosts.createIndex({ "mac_address": 1 }); 