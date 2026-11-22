package pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;

public class WatchlistPage extends BasePage {
    private static final By BTN_UPDATE = By.id("btn-update-watchlist");

    public WatchlistPage(WebDriver driver) {
        super(driver);
    }

    public WatchlistPage open() {
        go("/watchlist");
        return this;
    }

    public void update() {
        submit(BTN_UPDATE);
    }

    public boolean containsRecord(String code) {
        return isPresent(By.id("wl-row-" + code));
    }

    public int rowCount() {
        return driver.findElements(By.cssSelector("#tbl-watchlist-body tr")).size();
    }
}
