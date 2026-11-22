package pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;

/** Lich su sang loc (/screening-history). */
public class ScreeningHistoryPage extends BasePage {
    public ScreeningHistoryPage(WebDriver driver) {
        super(driver);
    }

    public ScreeningHistoryPage open() {
        go("/screening-history");
        return this;
    }

    /** So lan sang loc da duoc ghi nhan (lan bi chan boi K1 khong duoc ghi). */
    public int rowCount() {
        return retry(() -> driver.findElements(By.cssSelector("#tbl-screenings-body tr")).size());
    }
}
