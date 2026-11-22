package pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;

/** Man hinh Nhap lieu / Duyet ban ghi (/records). */
public class RecordsPage extends BasePage {
    private static final By BTN_ADD = By.id("btn-add");
    private static final By BTN_AUTHORIZE = By.id("btn-authorize");
    private static final By BTN_REJECT = By.id("btn-reject");
    private static final By SEARCH_FULLNAME = By.id("search_fullname");
    private static final By SEARCH_ID = By.id("search_id_number");
    private static final By BTN_SEARCH = By.id("btn-search");

    public RecordsPage(WebDriver driver) {
        super(driver);
    }

    public RecordsPage open() {
        go("/records");
        return this;
    }

    public void clickAdd() {
        submit(BTN_ADD);
    }

    public boolean hasRow(String code) {
        return isPresent(By.id("row-" + code));
    }

    public void selectRecord(String code) {
        click(By.id("chk-" + code));
    }

    public void authorizeSelected() {
        submit(BTN_AUTHORIZE);
    }

    public void rejectSelected() {
        submit(BTN_REJECT);
    }

    public void openDetail(String code) {
        submit(By.id("lnk-view-" + code));
    }

    public void searchByName(String name) {
        type(SEARCH_FULLNAME, name);
        submit(BTN_SEARCH);
    }

    public boolean canAdd() {
        return isActionable(BTN_ADD);
    }

    public boolean canAuthorize() {
        return isActionable(BTN_AUTHORIZE);
    }
}
