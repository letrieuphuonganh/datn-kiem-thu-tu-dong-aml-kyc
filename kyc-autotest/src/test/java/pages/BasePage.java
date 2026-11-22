package pages;

import config.Config;
import org.openqa.selenium.By;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.StaleElementReferenceException;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebDriverException;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.Select;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.time.Duration;
import java.util.List;
import java.util.function.Supplier;

/**
 * Lop cha cua moi Page Object: ham dung chung (cho, nhap, bam, doc thong bao). Khong dung Thread.sleep.
 * Cac thao tac gui form dung submit(): bam xong thi CHO den khi trang moi tai xong, tranh doc nham trang cu.
 */
public abstract class BasePage {
    protected final WebDriver driver;
    protected final WebDriverWait wait;

    // Cac phan tu co o moi man hinh (base.html)
    protected static final By MSG_SUCCESS = By.id("msg-success");
    protected static final By MSG_ERROR = By.id("msg-error");
    protected static final By CURRENT_USER = By.id("current-user");
    protected static final By BTN_LOGOUT = By.id("btn-logout");

    protected BasePage(WebDriver driver) {
        this.driver = driver;
        this.wait = new WebDriverWait(driver, Duration.ofSeconds(Config.TIMEOUT_SEC));
        // Trang vua chuyen/tai lai co the lam phan tu cu 'het hieu luc' (stale) hoac Chrome bao loi
        // "Node ... does not belong to the document": thu lai trong luc cho thay vi that bai ngay.
        this.wait.ignoring(WebDriverException.class);
    }

    // ---------- thu lai khi trang dang chuyen ----------
    /** Thu lai toi 3 lan neu phan tu het hieu luc do trang vua chuyen/tai lai. */
    protected <T> T retry(Supplier<T> action) {
        RuntimeException last = null;
        for (int i = 0; i < 3; i++) {
            try {
                return action.get();
            } catch (StaleElementReferenceException ex) {
                last = ex;
            } catch (WebDriverException ex) {
                String msg = ex.getMessage();
                if (msg != null && msg.contains("does not belong to the document")) {
                    last = ex;
                } else {
                    throw ex;
                }
            }
        }
        throw last;
    }

    protected void retryRun(Runnable action) {
        retry(() -> {
            action.run();
            return null;
        });
    }

    // ---------- thao tac co ban ----------
    public void go(String path) {
        driver.get(Config.BASE_URL + path);
    }

    protected WebElement find(By by) {
        return wait.until(ExpectedConditions.visibilityOfElementLocated(by));
    }

    protected void click(By by) {
        retryRun(() -> wait.until(ExpectedConditions.elementToBeClickable(by)).click());
    }

    /** Bam nut/lien ket gui form hoac chuyen trang, roi cho den khi trang cu bi thay bang trang moi. */
    protected void submit(By by) {
        WebElement oldPage = driver.findElement(By.tagName("html"));
        click(by);
        wait.until(ExpectedConditions.stalenessOf(oldPage));
    }

    protected void type(By by, String text) {
        retryRun(() -> {
            WebElement e = find(by);
            e.clear();
            if (text == null || text.isEmpty()) {
                return;
            }
            e.sendKeys(text);
            // Kiem tra lai: neu o khong nhan du chu thi dat gia tri bang JavaScript (du phong)
            String actual = e.getAttribute("value");
            if (!text.equals(actual)) {
                ((JavascriptExecutor) driver).executeScript(
                        "arguments[0].value = arguments[1];"
                        + "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));"
                        + "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));", e, text);
            }
        });
    }

    protected void selectByText(By by, String visibleText) {
        retryRun(() -> new Select(find(by)).selectByVisibleText(visibleText));
    }

    protected String text(By by) {
        return retry(() -> find(by).getText().trim());
    }

    /** Doc noi dung ke ca phan tu dang an (display:none). */
    protected String textContent(By by) {
        return retry(() -> wait.until(ExpectedConditions.presenceOfElementLocated(by))
                .getAttribute("textContent").trim());
    }

    public boolean isPresent(By by) {
        return !driver.findElements(by).isEmpty();
    }

    /** Co hien thi va bam duoc (khong bi disabled). */
    public boolean isActionable(By by) {
        return retry(() -> {
            List<WebElement> l = driver.findElements(by);
            return !l.isEmpty() && l.get(0).isDisplayed() && l.get(0).isEnabled();
        });
    }

    // ---------- thong bao chung ----------
    public String successMessage() {
        wait.until(ExpectedConditions.visibilityOfElementLocated(MSG_SUCCESS));
        return textContent(MSG_SUCCESS);
    }

    public boolean hasSuccessMessage() {
        try {
            List<WebElement> found = driver.findElements(MSG_SUCCESS);
            return !found.isEmpty() && found.get(0).isDisplayed();
        } catch (WebDriverException ex) {
            return false; // trang dang chuyen; lan kiem tra sau se doc lai
        }
    }

    /** Gom thong bao loi o msg-error va cac loi theo tung truong (.field-error). */
    public String allErrors() {
        StringBuilder sb = new StringBuilder();
        try {
            for (WebElement e : driver.findElements(By.cssSelector("#msg-error, .field-error"))) {
                String t = e.getAttribute("textContent");
                if (t != null && !t.trim().isEmpty()) {
                    sb.append(t.trim()).append(" | ");
                }
            }
        } catch (WebDriverException ex) {
            return ""; // trang dang chuyen; lan kiem tra sau se doc lai
        }
        return sb.toString();
    }

    /** Cho den khi thong bao loi chua noi dung mong doi; tra ve false neu het thoi gian cho. */
    public boolean waitErrorContains(String expected) {
        try {
            return wait.until(d -> allErrors().contains(expected));
        } catch (org.openqa.selenium.TimeoutException ex) {
            return false;
        }
    }

    public boolean waitSuccessContains(String expected) {
        try {
            return wait.until(d -> hasSuccessMessage() && textContent(MSG_SUCCESS).contains(expected));
        } catch (org.openqa.selenium.TimeoutException ex) {
            return false;
        }
    }

    // ---------- phien lam viec ----------
    public String currentUser() {
        return text(CURRENT_USER);
    }

    public void logout() {
        submit(BTN_LOGOUT);
    }
}
