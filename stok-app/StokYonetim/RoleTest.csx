using Microsoft.EntityFrameworkCore;
using StokYonetim.Data;
using StokYonetim.Models;

using var db = new AppDbContext();
var p = db.Personnel.AsNoTracking().FirstOrDefault(x => x.Id == 3);
if (p != null) Console.WriteLine($"Id={p.Id} Role=[{p.Role}] CreatedAt={p.CreatedAt:o}");
var test = new Personnel { FullName = "EF Test", Email = "", Phone = "", Salary = 0, Role = "Depo", CreatedAt = DateTime.UtcNow, UpdatedAt = DateTime.UtcNow };
db.Personnel.Add(test);
db.SaveChanges();
var read = db.Personnel.AsNoTracking().First(x => x.FullName == "EF Test");
Console.WriteLine($"Inserted Role=[{read.Role}]");
db.Personnel.Remove(db.Personnel.First(x => x.FullName == "EF Test"));
db.SaveChanges();
