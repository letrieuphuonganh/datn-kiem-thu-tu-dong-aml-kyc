package pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.support.ui.ExpectedConditions;

/** Man hinh Sang loc khach hang (/screening). */
public class ScreeningPage extends BasePage {
    private static final By CUSTOMER_TYPE = By.id("customer_type");
    private static final By FULLNAME = By.id("fullname");
    private static final By ID_NUMBER = By.id("id_number");
    private static final By BTN_SCREEN = By.id("btn-screen");
    private static final By RESULT_PANEL = By.id("screening-result");

    public ScreeningPage(WebDriver driver) {
        super(driver);
    }

    public ScreeningPage open() {
        go("/screening");
        return this;
    }

    public void screen(String customerType, String fullname, String idNumber) {
        if (customerType != null && !customerType.isEmpty()) {
            selectByText(CUSTOMER_TYPE, customerType);
        }
        type(FULLNAME, fullname);
        type(ID_NUMBER, idNumber);
        submit(BTN_SCREEN);
    }

    /** True neu khung "Ket qua sang loc" dang hien thi (sang loc thanh cong); false khi bi chan hoac nhap sai. */
    public boolean resultVisible() {
        return retry(() -> {
            java.util.List<org.openqa.selenium.WebElement> panel = driver.findElements(RESULT_PANEL);
            return !panel.isEmpty() && panel.get(0).isDisplayed();
        });
    }

    private void waitResult() {
        wait.until(ExpectedConditions.visibilityOfElementLocated(RESULT_PANEL));
    }

    /** "HIT" hoac "NO-HIT". */
    public String resultStatus() {
        waitResult();
        return text(By.id("result-status"));
    }

    public String resultMessage() {
        waitResult();
        return text(By.id("result-message"));
    }

    public String cifDecision() {
        waitResult();
        return text(By.id("result-cif-decision"));
    }

    /** Ma case (rong neu NO-HIT). */
    public String caseCode() {
        waitResult();
        return textContent(By.id("result-case-code"));
    }

    public int matchCount() {
        waitResult();
        return driver.findElements(By.cssSelector("#tbl-screening-matches-body tr")).size();
    }
}
