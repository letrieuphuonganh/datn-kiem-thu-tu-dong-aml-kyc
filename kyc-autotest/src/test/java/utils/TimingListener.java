package utils;

import org.openqa.selenium.OutputType;
import org.openqa.selenium.TakesScreenshot;
import org.openqa.selenium.WebDriver;
import org.testng.ITestContext;
import org.testng.ITestListener;
import org.testng.ITestResult;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

/**
 * Ghi thoi gian chay tung test ra target/timing.csv (dung cho chuong danh gia dinh luong)
 * va chup anh man hinh khi test that bai vao target/screenshots/.
 */
public class TimingListener implements ITestListener {
    private static final List<String> LINES = Collections.synchronizedList(new ArrayList<>());
    private static int passed, failed, skipped;
    private static long totalMs;

    @Override
    public void onTestSuccess(ITestResult r) {
        record(r, "PASSED");
        passed++;
    }

    @Override
    public void onTestFailure(ITestResult r) {
        record(r, "FAILED");
        failed++;
        screenshot(r);
    }

    @Override
    public void onTestSkipped(ITestResult r) {
        record(r, "SKIPPED");
        skipped++;
    }

    @Override
    public void onFinish(ITestContext ctx) {
        List<String> out = new ArrayList<>();
        out.add("Test,Parameters,Status,DurationMs");
        out.addAll(LINES);
        try {
            Path p = Paths.get("target", "timing.csv");
            Files.createDirectories(p.getParent());
            Files.write(p, out, StandardCharsets.UTF_8);
        } catch (IOException e) {
            System.err.println("Khong ghi duoc timing.csv: " + e.getMessage());
        }
        System.out.printf("%n=== TONG KET: %d test | Passed %d | Failed %d | Skipped %d | Tong thoi gian %.1f giay ===%n",
                passed + failed + skipped, passed, failed, skipped, totalMs / 1000.0);
    }

    private void record(ITestResult r, String status) {
        long ms = r.getEndMillis() - r.getStartMillis();
        totalMs += ms;
        String params = r.getParameters() == null ? "" : Arrays.deepToString(r.getParameters());
        LINES.add(csv(r.getMethod().getMethodName()) + "," + csv(params) + "," + status + "," + ms);
    }

    private void screenshot(ITestResult r) {
        WebDriver d = DriverManager.get();
        if (d == null) return;
        try {
            Path dir = Paths.get("target", "screenshots");
            Files.createDirectories(dir);
            String name = r.getMethod().getMethodName() + "_" + System.currentTimeMillis() + ".png";
            Files.copy(((TakesScreenshot) d).getScreenshotAs(OutputType.FILE).toPath(),
                    dir.resolve(name), StandardCopyOption.REPLACE_EXISTING);
        } catch (Exception e) {
            System.err.println("Khong chup duoc anh: " + e.getMessage());
        }
    }

    private static String csv(String s) {
        return "\"" + s.replace("\"", "\"\"") + "\"";
    }
}
