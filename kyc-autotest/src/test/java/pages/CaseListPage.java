package pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;

/** Danh sach Case (/cases). */
public class CaseListPage extends BasePage {
    public CaseListPage(WebDriver driver) {
        super(driver);
    }

    public CaseListPage open() {
        go("/cases");
        return this;
    }

    public int rowCount() {
        return retry(() -> driver.findElements(By.cssSelector("#tbl-cases-body tr")).size());
    }
}
