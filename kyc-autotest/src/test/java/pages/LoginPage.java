package pages;

import config.Config;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.support.ui.ExpectedConditions;

public class LoginPage extends BasePage {
    private static final By USERNAME = By.id("username");
    private static final By PASSWORD = By.id("password");
    private static final By BTN_LOGIN = By.id("btn-login");

    public LoginPage(WebDriver driver) {
        super(driver);
    }

    public void login(String user, String pass) {
        type(USERNAME, user);
        type(PASSWORD, pass);
        submit(BTN_LOGIN);
    }

    /** Dang nhap bang tai khoan demo; neu dang dang nhap tai khoan khac thi dang xuat truoc. */
    public void loginAs(String user) {
        go("/login");
        if (isPresent(CURRENT_USER)) {
            if (currentUser().contains(user)) {
                return;
            }
            logout();
            go("/login");
        }
        login(user, Config.PASSWORD);
        wait.until(ExpectedConditions.textToBePresentInElementLocated(CURRENT_USER, user));
    }
}
