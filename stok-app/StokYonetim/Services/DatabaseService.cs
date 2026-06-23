using System.Data;

using Microsoft.EntityFrameworkCore;

using StokYonetim.Data;

using StokYonetim.Models;



namespace StokYonetim.Services;



public static class DatabaseService

{

    public static void Initialize()

    {

        using var db = new AppDbContext();

        db.Database.EnsureCreated();

        EnsureAppUsersTable(db);

        MigrateAdminUsersToAppUsers(db);

        EnsurePersonnelTable(db);

        EnsurePersonnelRoleColumn(db);

        FixPersonnelRoleColumnOrder(db);

        EnsurePersonnelIsActiveColumn(db);

        EnsurePersonnelPaymentsTable(db);

        EnsureFinanceEntriesTable(db);

        EnsureAppSettingsTable(db);

        EnsureOrdersTables(db);

        EnsureOrderItemUnitPriceColumn(db);

        EnsureProductUnitPriceColumn(db);

        SyncAdminFromConfig(db);

    }



    private static void EnsureAppUsersTable(AppDbContext db)

    {

        db.Database.ExecuteSqlRaw("""

            CREATE TABLE IF NOT EXISTS AppUsers (

                Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,

                Email TEXT NOT NULL,

                PasswordHash TEXT NOT NULL,

                Role TEXT NOT NULL DEFAULT 'Çalışan',

                CreatedAt TEXT NOT NULL,

                UpdatedAt TEXT NOT NULL

            );

            """);



        db.Database.ExecuteSqlRaw("""

            CREATE UNIQUE INDEX IF NOT EXISTS IX_AppUsers_Email ON AppUsers(Email);

            """);

    }



    private static void MigrateAdminUsersToAppUsers(AppDbContext db)

    {

        var connection = db.Database.GetDbConnection();

        if (connection.State != ConnectionState.Open)

            connection.Open();



        if (!TableExists(connection, "AdminUsers") || TableHasRows(connection, "AppUsers"))

            return;



        using var command = connection.CreateCommand();

        command.CommandText = "SELECT Email, PasswordHash, CreatedAt FROM AdminUsers";

        using var reader = command.ExecuteReader();



        while (reader.Read())

        {

            var email = reader.GetString(0);

            var hash = reader.GetString(1);

            var createdAt = reader.GetString(2);

            var updatedAt = createdAt;



            db.Database.ExecuteSqlRaw(

                "INSERT INTO AppUsers (Email, PasswordHash, Role, CreatedAt, UpdatedAt) VALUES ({0}, {1}, {2}, {3}, {4})",

                email, hash, UserRoles.Yonetici, createdAt, updatedAt);

        }

    }



    private static void EnsurePersonnelTable(AppDbContext db)

    {

        db.Database.ExecuteSqlRaw("""

            CREATE TABLE IF NOT EXISTS Personnel (

                Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,

                FullName TEXT NOT NULL,

                Email TEXT NOT NULL DEFAULT '',

                Phone TEXT NOT NULL DEFAULT '',

                BirthDate TEXT NULL,

                Salary REAL NOT NULL DEFAULT 0,

                Role TEXT NOT NULL DEFAULT 'Çalışan',

                CreatedAt TEXT NOT NULL,

                UpdatedAt TEXT NOT NULL

            );

            """);

    }



    private static void EnsurePersonnelRoleColumn(AppDbContext db)

    {

        var connection = db.Database.GetDbConnection();

        if (connection.State != ConnectionState.Open)

            connection.Open();



        using var command = connection.CreateCommand();

        command.CommandText = "PRAGMA table_info(Personnel)";

        using var reader = command.ExecuteReader();



        var hasRole = false;

        while (reader.Read())

        {

            if (reader.GetString(1) == "Role")

            {

                hasRole = true;

                break;

            }

        }



        if (!hasRole)

        {

            db.Database.ExecuteSqlRaw(

                "ALTER TABLE Personnel ADD COLUMN Role TEXT NOT NULL DEFAULT 'Çalışan'");

        }

    }



    private static void FixPersonnelRoleColumnOrder(AppDbContext db)

    {

        var connection = db.Database.GetDbConnection();

        if (connection.State != ConnectionState.Open)

            connection.Open();



        var columns = new List<(int Ord, string Name)>();

        using (var command = connection.CreateCommand())

        {

            command.CommandText = "PRAGMA table_info(Personnel)";

            using var reader = command.ExecuteReader();

            while (reader.Read())

                columns.Add((reader.GetInt32(0), reader.GetString(1)));

        }



        var roleColumn = columns.FirstOrDefault(c => c.Name == "Role");

        var updatedAtColumn = columns.FirstOrDefault(c => c.Name == "UpdatedAt");

        if (roleColumn.Name is null || updatedAtColumn.Name is null)

            return;



        if (roleColumn.Ord <= updatedAtColumn.Ord)

            return;



        db.Database.ExecuteSqlRaw("""

            CREATE TABLE Personnel_mig (

                Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,

                FullName TEXT NOT NULL,

                Email TEXT NOT NULL DEFAULT '',

                Phone TEXT NOT NULL DEFAULT '',

                BirthDate TEXT NULL,

                Salary REAL NOT NULL DEFAULT 0,

                Role TEXT NOT NULL DEFAULT 'Çalışan',

                CreatedAt TEXT NOT NULL,

                UpdatedAt TEXT NOT NULL

            );

            """);



        db.Database.ExecuteSqlRaw("""

            INSERT INTO Personnel_mig (Id, FullName, Email, Phone, BirthDate, Salary, Role, CreatedAt, UpdatedAt)

            SELECT Id, FullName, Email, Phone, BirthDate, Salary, Role, CreatedAt, UpdatedAt FROM Personnel;

            """);



        db.Database.ExecuteSqlRaw("DROP TABLE Personnel;");

        db.Database.ExecuteSqlRaw("ALTER TABLE Personnel_mig RENAME TO Personnel;");

    }



    private static void EnsurePersonnelIsActiveColumn(AppDbContext db)
    {
        var connection = db.Database.GetDbConnection();
        if (connection.State != ConnectionState.Open)
            connection.Open();

        using var command = connection.CreateCommand();
        command.CommandText = "PRAGMA table_info(Personnel)";
        using var reader = command.ExecuteReader();

        var hasIsActive = false;
        while (reader.Read())
        {
            if (reader.GetString(1) == "IsActive")
            {
                hasIsActive = true;
                break;
            }
        }

        if (!hasIsActive)
        {
            db.Database.ExecuteSqlRaw(
                "ALTER TABLE Personnel ADD COLUMN IsActive INTEGER NOT NULL DEFAULT 1");
        }
    }

    private static void EnsurePersonnelPaymentsTable(AppDbContext db)
    {
        db.Database.ExecuteSqlRaw("""
            CREATE TABLE IF NOT EXISTS PersonnelPayments (
                Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                PersonnelId INTEGER NOT NULL,
                PaymentType TEXT NOT NULL,
                Amount REAL NOT NULL DEFAULT 0,
                CreatedAt TEXT NOT NULL,
                FOREIGN KEY (PersonnelId) REFERENCES Personnel(Id) ON DELETE CASCADE
            );
            """);
    }

    private static void EnsureFinanceEntriesTable(AppDbContext db)
    {
        db.Database.ExecuteSqlRaw("""
            CREATE TABLE IF NOT EXISTS FinanceEntries (
                Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                EntryType TEXT NOT NULL,
                Category TEXT NOT NULL,
                Description TEXT NOT NULL,
                Amount REAL NOT NULL DEFAULT 0,
                ReferenceType TEXT NULL,
                ReferenceId INTEGER NULL,
                CreatedAt TEXT NOT NULL
            );
            """);
    }

    private static void EnsureAppSettingsTable(AppDbContext db)
    {
        db.Database.ExecuteSqlRaw("""
            CREATE TABLE IF NOT EXISTS AppSettings (
                Id INTEGER NOT NULL PRIMARY KEY CHECK (Id = 1),
                SalaryPaymentDay INTEGER NOT NULL DEFAULT 1
            );
            """);

        db.Database.ExecuteSqlRaw("""
            INSERT OR IGNORE INTO AppSettings (Id, SalaryPaymentDay) VALUES (1, 1);
            """);
    }

    private static void EnsureOrdersTables(AppDbContext db)

    {

        db.Database.ExecuteSqlRaw("""

            CREATE TABLE IF NOT EXISTS Orders (

                Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,

                CustomerName TEXT NOT NULL DEFAULT '',

                CustomerPhone TEXT NOT NULL DEFAULT '',

                Notes TEXT NOT NULL DEFAULT '',

                CreatedAt TEXT NOT NULL,

                UpdatedAt TEXT NOT NULL

            );

            """);



        db.Database.ExecuteSqlRaw("""

            CREATE TABLE IF NOT EXISTS OrderItems (

                Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,

                OrderId INTEGER NOT NULL,

                ProductId INTEGER NOT NULL,

                Quantity INTEGER NOT NULL DEFAULT 1,

                UnitPrice REAL NOT NULL DEFAULT 0,

                FOREIGN KEY (OrderId) REFERENCES Orders(Id) ON DELETE CASCADE,

                FOREIGN KEY (ProductId) REFERENCES Products(Id) ON DELETE RESTRICT

            );

            """);

    }



    private static void EnsureOrderItemUnitPriceColumn(AppDbContext db)

    {

        var connection = db.Database.GetDbConnection();

        if (connection.State != ConnectionState.Open)

            connection.Open();



        using var command = connection.CreateCommand();

        command.CommandText = "PRAGMA table_info(OrderItems)";

        using var reader = command.ExecuteReader();



        var hasUnitPrice = false;

        while (reader.Read())

        {

            if (reader.GetString(1) == "UnitPrice")

            {

                hasUnitPrice = true;

                break;

            }

        }



        if (!hasUnitPrice)

        {

            db.Database.ExecuteSqlRaw(

                "ALTER TABLE OrderItems ADD COLUMN UnitPrice REAL NOT NULL DEFAULT 0");

        }

    }



    private static void EnsureProductUnitPriceColumn(AppDbContext db)
    {
        var connection = db.Database.GetDbConnection();
        if (connection.State != ConnectionState.Open)
            connection.Open();

        using var command = connection.CreateCommand();
        command.CommandText = "PRAGMA table_info(Products)";
        using var reader = command.ExecuteReader();

        var hasUnitPrice = false;
        while (reader.Read())
        {
            if (reader.GetString(1) == "UnitPrice")
            {
                hasUnitPrice = true;
                break;
            }
        }

        if (!hasUnitPrice)
        {
            db.Database.ExecuteSqlRaw(
                "ALTER TABLE Products ADD COLUMN UnitPrice REAL NOT NULL DEFAULT 0");
        }
    }

    private static void SyncAdminFromConfig(AppDbContext db)

    {

        var admin = AppServices.Instance.Config.Admin;

        if (string.IsNullOrWhiteSpace(admin.Email) || string.IsNullOrWhiteSpace(admin.Password))

            return;



        var email = admin.Email.Trim().ToLowerInvariant();

        var hash = PasswordHasher.Hash(admin.Password);

        var now = DateTime.UtcNow.ToString("o");



        var existing = db.AppUsers

            .AsEnumerable()

            .FirstOrDefault(u => u.Email.Trim().ToLowerInvariant() == email);



        if (existing != null)

        {

            existing.PasswordHash = hash;

            existing.Role = UserRoles.Yonetici;

            existing.UpdatedAt = DateTime.UtcNow;

            db.SaveChanges();

            return;

        }



        db.AppUsers.Add(new AppUser

        {

            Email = email,

            PasswordHash = hash,

            Role = UserRoles.Yonetici,

            CreatedAt = DateTime.UtcNow,

            UpdatedAt = DateTime.UtcNow

        });

        db.SaveChanges();

    }



    private static bool TableExists(IDbConnection connection, string tableName)

    {

        using var command = connection.CreateCommand();

        command.CommandText = "SELECT name FROM sqlite_master WHERE type='table' AND name=$name";

        var param = command.CreateParameter();

        param.ParameterName = "$name";

        param.Value = tableName;

        command.Parameters.Add(param);

        return command.ExecuteScalar() != null;

    }



    private static bool TableHasRows(IDbConnection connection, string tableName)

    {

        using var command = connection.CreateCommand();

        command.CommandText = $"SELECT COUNT(*) FROM {tableName}";

        return Convert.ToInt32(command.ExecuteScalar()) > 0;

    }

}


