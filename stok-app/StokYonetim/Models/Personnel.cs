namespace StokYonetim.Models;

public class Personnel
{
    public int Id { get; set; }
    public string FullName { get; set; } = "";
    public string Email { get; set; } = "";
    public string Phone { get; set; } = "";
    public DateTime? BirthDate { get; set; }
    public decimal Salary { get; set; }
    public string Role { get; set; } = PersonnelRoles.Calisan;
    public bool IsActive { get; set; } = true;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
}
