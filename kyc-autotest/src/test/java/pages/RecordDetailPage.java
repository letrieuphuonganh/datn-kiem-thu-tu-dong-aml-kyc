package pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;

/** Man hinh xem chi tiet ban ghi (/records/<ma>). */
public class RecordDetailPage extends BasePage {
    public RecordDetailPage(WebDriver driver) {
        super(driver);
    }

    public RecordDetailPage open(String code) {
        go("/records/" + code);
        return this;
    }

    public String authStatus() {
        return text(By.id("view-auth_status"));
    }

    public String activeStatus() {
        return text(By.id("view-active_status"));
    }

    public String fullname() {
        return text(By.id("view-fullname"));
    }

    public boolean inWatchlist() {
        return text(By.id("view-in_watchlist")).equals("Có");
    }
}
