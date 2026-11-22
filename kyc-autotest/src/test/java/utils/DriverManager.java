package utils;

import config.Config;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/** Giu WebDriver theo luong (ThreadLocal) de BaseTest va Listener cung dung duoc. */
public final class DriverManager {
    private static final ThreadLocal<WebDriver> TL = new ThreadLocal<>();

    private DriverManager() {}

    public static void start() {
        ChromeOptions options = new ChromeOptions();
        options.addArguments("--window-size=1366,900", "--disable-notifications");
        // Tat hop thoai luu mat khau / canh bao mat khau bi lo cua Chrome (de chiem focus, lam mat phim go)
        Map<String, Object> prefs = new HashMap<>();
        prefs.put("credentials_enable_service", false);
        prefs.put("profile.password_manager_enabled", false);
        prefs.put("profile.password_manager_leak_detection", false);
        options.setExperimentalOption("prefs", prefs);
        options.setExperimentalOption("excludeSwitches", List.of("enable-automation"));
        if (Config.HEADLESS) {
            options.addArguments("--headless=new");
        }
        TL.set(new ChromeDriver(options)); // Selenium Manager tu tai ChromeDriver
    }

    public static WebDriver get() {
        return TL.get();
    }

    public static void quit() {
        WebDriver d = TL.get();
        if (d != null) {
            d.quit();
            TL.remove();
        }
    }
}
