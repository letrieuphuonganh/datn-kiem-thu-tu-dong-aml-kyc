package pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;

/** Hop thu gia lap (/mailbox): moi nguoi chi thay email gui cho minh. */
public class MailboxPage extends BasePage {
    public MailboxPage(WebDriver driver) {
        super(driver);
    }

    public MailboxPage open() {
        go("/mailbox");
        return this;
    }

    public int emailCount() {
        return driver.findElements(By.cssSelector("#tbl-emails-body tr")).size();
    }

    public String allEmailsText() {
        if (!isPresent(By.id("tbl-emails-body"))) {
            return "";
        }
        return textContent(By.id("tbl-emails-body"));
    }
}
