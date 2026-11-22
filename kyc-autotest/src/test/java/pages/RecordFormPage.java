package pages;

import org.openqa.selenium.By;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.TimeoutException;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.time.Duration;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Form Them moi / Sua ban ghi (/records/new). */
public class RecordFormPage extends BasePage {
    private static final By SUBJECT_TYPE = By.id("subject_type");
    private static final By FULLNAME = By.id("fullname");
    private static final By ID_NUMBER = By.id("id_number");
    private static final By BIRTH_YEAR = By.id("birth_year");
    private static final By NATIONALITY = By.id("nationality");
    private static final By REASON = By.id("reason");
    private static final By ACTIVE_STATUS = By.id("active_status");
    private static final By BTN_SAVE = By.id("btn-save");
    private static final By SAVED_CODE = By.id("saved-record-code");

    public RecordFormPage(WebDriver driver) {
        super(driver);
    }

    public RecordFormPage open() {
        go("/records/new");
        return this;
    }

    public RecordFormPage fill(String subjectType, String fullname, String idNumber, String birthYear) {
        if (subjectType != null && !subjectType.isEmpty()) {
            selectByText(SUBJECT_TYPE, subjectType);
        }
        type(FULLNAME, fullname);
        type(ID_NUMBER, idNumber);
        type(BIRTH_YEAR, birthYear);
        return this;
    }

    public RecordFormPage fillOptional(String nationality, String reason, String activeStatus) {
        type(NATIONALITY, nationality);
        type(REASON, reason);
        if (activeStatus != null && !activeStatus.isEmpty()) {
            selectByText(ACTIVE_STATUS, activeStatus);
        }
        return this;
    }

    public void save() {
        WebElement oldPage = driver.findElement(By.tagName("html"));
        click(BTN_SAVE);
        try {
            new WebDriverWait(driver, Duration.ofSeconds(5)).until(ExpectedConditions.stalenessOf(oldPage));
        } catch (TimeoutException ex) {
            // Du phong: form chua duoc gui thi gui bang JavaScript
            ((JavascriptExecutor) driver).executeScript("document.getElementById('frm-record').requestSubmit();");
            wait.until(ExpectedConditions.stalenessOf(oldPage));
        }
    }

    /** Ma ban ghi vua luu (WL-xxxx): doc tu phan tu an saved-record-code, neu rong thi tim trong thong bao. */
    public String savedCode() {
        successMessage(); // cho thong bao thanh cong xuat hien
        String code = textContent(SAVED_CODE);
        if (code.isEmpty()) {
            Matcher m = Pattern.compile("WL-\\d+").matcher(textContent(MSG_SUCCESS));
            if (m.find()) {
                code = m.group();
            }
        }
        if (code.isEmpty()) {
            throw new IllegalStateException("Khong lay duoc ma ban ghi vua luu");
        }
        return code;
    }
}
