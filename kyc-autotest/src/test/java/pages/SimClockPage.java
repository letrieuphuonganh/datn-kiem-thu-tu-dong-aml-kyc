package pages;

import org.openqa.selenium.WebDriver;

/** Dong ho gia lap cua web demo (/set-date). Dung de kiem thu cac kich ban theo ngay ma khong phai cho qua ngay that. */
public class SimClockPage extends BasePage {
    public SimClockPage(WebDriver driver) {
        super(driver);
    }

    /** Gia lap da qua {@code days} ngay ke tu ngay that (0 = ngay that). /reset-data cung dat lai ve 0. */
    public void setDayOffset(int days) {
        go("/set-date?offset=" + days);
        if (!waitSuccessContains("Ngày giả lập")) {
            throw new AssertionError("Khong dat duoc ngay gia lap: " + allErrors());
        }
    }
}
