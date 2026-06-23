using System.Windows;
using System.Windows.Controls;
using StokYonetim.Services;
using StokYonetim.Views;
using StokYonetim.Views.Pages;

namespace StokYonetim;

public partial class MainWindow : Window
{
    private readonly CategoriesPage _categoriesPage = new();
    private readonly ProductsPage _productsPage = new();
    private readonly StockPage _stockPage = new();
    private readonly PersonnelPage _personnelPage = new();
    private readonly UsersPage _usersPage = new();
    private readonly OrderAddPage _orderAddPage = new();
    private readonly OrdersListPage _ordersListPage = new();
    private readonly FinancePage _financePage = new();

    public MainWindow()
    {
        InitializeComponent();
        ApplyNavigation();
        ShowPage(AuthorizationService.DefaultPageForRole(CurrentUserService.Current?.Role));
    }

    private void ApplyNavigation()
    {
        var role = CurrentUserService.Current?.Role;

        NavCategories.Visibility = AuthorizationService.CanAccessCategories(role)
            ? Visibility.Visible : Visibility.Collapsed;
        NavProducts.Visibility = AuthorizationService.CanAccessProducts(role)
            ? Visibility.Visible : Visibility.Collapsed;
        NavStock.Visibility = AuthorizationService.CanAccessStock(role)
            ? Visibility.Visible : Visibility.Collapsed;
        NavPersonnel.Visibility = AuthorizationService.CanAccessPersonnel(role)
            ? Visibility.Visible : Visibility.Collapsed;
        NavUsers.Visibility = AuthorizationService.CanAccessUsers(role)
            ? Visibility.Visible : Visibility.Collapsed;
        NavOrderAdd.Visibility = AuthorizationService.CanAccessOrderAdd(role)
            ? Visibility.Visible : Visibility.Collapsed;
        NavOrders.Visibility = AuthorizationService.CanAccessOrdersList(role)
            ? Visibility.Visible : Visibility.Collapsed;
        NavFinance.Visibility = AuthorizationService.CanAccessFinance(role)
            ? Visibility.Visible : Visibility.Collapsed;

        _productsPage.ApplyAccessMode();
        _stockPage.ApplyAccessMode();
        _personnelPage.ApplyAccessMode();
        _ordersListPage.ApplyAccessMode();
    }

    private void Nav_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button btn && btn.Tag is string tag)
            ShowPage(tag);
    }

    private void Logout_Click(object sender, RoutedEventArgs e)
    {
        CurrentUserService.Clear();
        var login = new LoginWindow();
        login.Show();
        Close();
    }

    private void ShowPage(string page)
    {
        var role = CurrentUserService.Current?.Role;

        NavCategories.Style = (Style)FindResource("NavButton");
        NavProducts.Style = (Style)FindResource("NavButton");
        NavStock.Style = (Style)FindResource("NavButton");
        NavPersonnel.Style = (Style)FindResource("NavButton");
        NavUsers.Style = (Style)FindResource("NavButton");
        NavOrderAdd.Style = (Style)FindResource("NavButton");
        NavOrders.Style = (Style)FindResource("NavButton");
        NavFinance.Style = (Style)FindResource("NavButton");

        if (page == "products" && AuthorizationService.CanAccessProducts(role))
        {
            NavProducts.Style = (Style)FindResource("NavButtonActive");
            _productsPage.Refresh();
            PageHost.Content = _productsPage;
            return;
        }

        if (page == "stock" && AuthorizationService.CanAccessStock(role))
        {
            NavStock.Style = (Style)FindResource("NavButtonActive");
            _stockPage.Refresh();
            PageHost.Content = _stockPage;
            return;
        }

        if (page == "personnel" && AuthorizationService.CanAccessPersonnel(role))
        {
            NavPersonnel.Style = (Style)FindResource("NavButtonActive");
            _personnelPage.Refresh();
            PageHost.Content = _personnelPage;
            return;
        }

        if (page == "users" && AuthorizationService.CanAccessUsers(role))
        {
            NavUsers.Style = (Style)FindResource("NavButtonActive");
            _usersPage.Refresh();
            PageHost.Content = _usersPage;
            return;
        }

        if (page == "order-add" && AuthorizationService.CanAccessOrderAdd(role))
        {
            NavOrderAdd.Style = (Style)FindResource("NavButtonActive");
            _orderAddPage.Refresh();
            PageHost.Content = _orderAddPage;
            return;
        }

        if (page == "orders" && AuthorizationService.CanAccessOrdersList(role))
        {
            NavOrders.Style = (Style)FindResource("NavButtonActive");
            _ordersListPage.Refresh();
            PageHost.Content = _ordersListPage;
            return;
        }

        if (page == "finance" && AuthorizationService.CanAccessFinance(role))
        {
            NavFinance.Style = (Style)FindResource("NavButtonActive");
            _financePage.Refresh();
            PageHost.Content = _financePage;
            return;
        }

        if ((page == "categories" || page == "") && AuthorizationService.CanAccessCategories(role))
        {
            NavCategories.Style = (Style)FindResource("NavButtonActive");
            _categoriesPage.Refresh();
            PageHost.Content = _categoriesPage;
            return;
        }

        var fallback = AuthorizationService.DefaultPageForRole(role);
        if (!string.Equals(fallback, page, StringComparison.Ordinal))
            ShowPage(fallback);
    }
}
