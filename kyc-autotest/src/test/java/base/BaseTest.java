package base;

import config.Config;
import org.openqa.selenium.WebDriver;
import org.testng.annotations.AfterMethod;
import org.testng.annotations.BeforeMethod;
import utils.DriverManager;

/** Moi test chay tren trinh duyet moi va du lieu demo duoc dat lai (/reset-data) -> cac test doc lap nhau. */
public abstract class BaseTest {
    protected WebDriver driver;

    @BeforeMethod(alwaysRun = true)
    public void setUp() {
        DriverManager.start();
        driver = DriverManager.get();
        driver.get(Config.BASE_URL + "/reset-data");
    }

    @AfterMethod(alwaysRun = true)
    public void tearDown() {
        DriverManager.quit();
    }
}
