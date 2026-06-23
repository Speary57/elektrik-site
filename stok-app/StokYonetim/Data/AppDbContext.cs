using System.IO;
using Microsoft.EntityFrameworkCore;
using StokYonetim.Models;

namespace StokYonetim.Data;

public class AppDbContext : DbContext
{
    public DbSet<Category> Categories => Set<Category>();
    public DbSet<Product> Products => Set<Product>();
    public DbSet<AppUser> AppUsers => Set<AppUser>();
    public DbSet<Personnel> Personnel => Set<Personnel>();
    public DbSet<PersonnelPayment> PersonnelPayments => Set<PersonnelPayment>();
    public DbSet<FinanceEntry> FinanceEntries => Set<FinanceEntry>();
    public DbSet<AppSettings> AppSettings => Set<AppSettings>();
    public DbSet<Order> Orders => Set<Order>();
    public DbSet<OrderItem> OrderItems => Set<OrderItem>();

    private readonly string _dbPath;

    public AppDbContext()
    {
        var dir = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "KilaguzElektrik");
        Directory.CreateDirectory(dir);
        _dbPath = Path.Combine(dir, "stok.db");
    }

    protected override void OnConfiguring(DbContextOptionsBuilder options)
    {
        options.UseSqlite($"Data Source={_dbPath}");
    }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Category>(e =>
        {
            e.HasIndex(x => x.Name).IsUnique();
        });

        modelBuilder.Entity<Product>(e =>
        {
            e.Property(x => x.UnitPrice).HasColumnType("REAL");
            e.HasOne(x => x.Category)
                .WithMany(x => x.Products)
                .HasForeignKey(x => x.CategoryId)
                .OnDelete(DeleteBehavior.Cascade);
        });

        modelBuilder.Entity<AppUser>(e =>
        {
            e.HasIndex(x => x.Email).IsUnique();
        });

        modelBuilder.Entity<Personnel>(e =>
        {
            e.Property(x => x.Salary).HasColumnType("REAL");
            e.Property(x => x.Role).IsRequired().HasMaxLength(32);
        });

        modelBuilder.Entity<PersonnelPayment>(e =>
        {
            e.Property(x => x.Amount).HasColumnType("REAL");
            e.Property(x => x.PaymentType).IsRequired().HasMaxLength(32);

            e.HasOne(x => x.Personnel)
                .WithMany()
                .HasForeignKey(x => x.PersonnelId)
                .OnDelete(DeleteBehavior.Cascade);
        });

        modelBuilder.Entity<FinanceEntry>(e =>
        {
            e.Property(x => x.Amount).HasColumnType("REAL");
            e.Property(x => x.EntryType).IsRequired().HasMaxLength(16);
            e.Property(x => x.Category).IsRequired().HasMaxLength(32);
            e.Property(x => x.Description).IsRequired().HasMaxLength(500);
        });

        modelBuilder.Entity<OrderItem>(e =>
        {
            e.Property(x => x.UnitPrice).HasColumnType("REAL");

            e.HasOne(x => x.Order)
                .WithMany(x => x.Items)
                .HasForeignKey(x => x.OrderId)
                .OnDelete(DeleteBehavior.Cascade);

            e.HasOne(x => x.Product)
                .WithMany()
                .HasForeignKey(x => x.ProductId)
                .OnDelete(DeleteBehavior.Restrict);
        });
    }
}
