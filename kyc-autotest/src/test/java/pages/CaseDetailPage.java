package pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;

/** Chi tiet Case (/cases/<ma>): Maker danh gia Event + De xuat, Checker xu ly. */
public class CaseDetailPage extends BasePage {
    private static final By STATUS = By.id("case-status");
    private static final By CIF = By.id("case-cif-decision");
    private static final By SUPPLEMENT_NOTE = By.id("supplement_note");
    private static final By DECISION_REASON = By.id("decision_reason");

    public static final By BTN_PROPOSE = By.id("btn-propose");
    public static final By BTN_SEND_SUPPLEMENT = By.id("btn-send-supplement");
    public static final By BTN_REQUEST_SUPPLEMENT = By.id("btn-request-supplement");
    public static final By BTN_CLOSE_FALSE_HIT = By.id("btn-close-false-hit");
    public static final By BTN_CLOSE_TERMINATE = By.id("btn-close-terminate");
    public static final By BTN_CLOSE_MAINTAIN = By.id("btn-close-maintain");

    public CaseDetailPage(WebDriver driver) {
        super(driver);
    }

    public CaseDetailPage open(String caseCode) {
        go("/cases/" + caseCode);
        return this;
    }

    /** Danh gia Event thu n (n tinh tu 1): "Hit đúng" hoac "Hit sai", kem ly do. */
    public CaseDetailPage evaluateEvent(int n, String evaluation, String reason) {
        selectByText(By.id("eval-" + n), evaluation);
        type(By.id("reason-" + n), reason);
        return this;
    }

    public CaseDetailPage setDecisionReason(String reason) {
        type(DECISION_REASON, reason);
        return this;
    }

    public CaseDetailPage setSupplementNote(String note) {
        type(SUPPLEMENT_NOTE, note);
        return this;
    }

    public void clickButton(By button) {
        submit(button);
    }

    public String status() {
        return text(STATUS);
    }

    public String cifDecision() {
        return text(CIF);
    }

    /** Cho den khi trang thai Case dat gia tri mong doi (toi da het thoi gian cho), tra ve trang thai hien tai. */
    public String waitForStatus(String expected) {
        try {
            wait.until(d -> expected.equals(textContent(STATUS)));
        } catch (org.openqa.selenium.TimeoutException ex) {
            // het thoi gian cho: tra ve trang thai hien tai de assert bao loi ro rang
        }
        return status();
    }

    public int eventCount() {
        return driver.findElements(By.cssSelector("#tbl-events-body tr")).size();
    }

    public boolean canDo(By button) {
        return isActionable(button);
    }
}
