package tests;

import base.BaseTest;
import config.Config;
import org.testng.Assert;
import org.testng.annotations.DataProvider;
import org.testng.annotations.Test;
import pages.CaseDetailPage;
import pages.CaseListPage;
import pages.LoginPage;
import pages.ScreeningHistoryPage;
import pages.ScreeningPage;
import pages.SimClockPage;

/**
 * Script 8-12 (mo rong theo gop y cua GVHD): kiem soat sang loc lap lai theo dinh danh va theo ngay.
 * K1: cung mot dinh danh bi HIT toi da 3 lan/ngay (MAX_HIT_PER_DAY cua web demo), lan thu 4 bi chan.
 * K2: dinh danh dang co Case chua dong thi HIT lap lai khong tao Case moi.
 * Dong ho gia lap /set-date de kiem thu cac kich ban qua ngay.
 */
public class RepeatControlTest extends BaseTest {
    /** Khach hang mau "Tran Thi B": trung 2 ban ghi Watchlist (CCCD + ho ten) nen sinh 2 Event. */
    private static final String TYPE = "Cá nhân";
    private static final String NAME = "Tran Thi B";
    private static final String ID = "001987654321";

    /** Gioi han K1 cua web demo (MAX_HIT_PER_DAY). */
    private static final int LIMIT = 3;

    private ScreeningPage makerOpensScreening() {
        new LoginPage(driver).loginAs(Config.MAKER);
        return new ScreeningPage(driver);
    }

    @Test(description = "K2: sang loc HIT lap lai khi Case dang mo thi gan vao Case cu, khong tao Case moi")
    public void repeatedHit_attachesToOpenCase() {
        ScreeningPage screening = makerOpensScreening();

        screening.open().screen(TYPE, NAME, ID);
        Assert.assertEquals(screening.resultStatus(), "HIT", "Lan 1");
        String firstCase = screening.caseCode();
        int events = screening.matchCount();
        Assert.assertFalse(firstCase.isEmpty(), "Lan 1 phai tao Case");

        screening.open().screen(TYPE, NAME, ID);
        Assert.assertEquals(screening.resultStatus(), "HIT", "Lan 2");
        Assert.assertEquals(screening.caseCode(), firstCase, "Lan 2 phai gan vao Case cu");
        Assert.assertEquals(screening.matchCount(), events, "So Event giu nguyen");
        Assert.assertTrue(screening.waitSuccessContains("đang xử lý"),
                "Thong bao K2 khong hien thi: " + screening.allErrors());

        Assert.assertEquals(new CaseListPage(driver).open().rowCount(), 1, "Chi co 1 Case");
        Assert.assertEquals(new ScreeningHistoryPage(driver).open().rowCount(), 2, "Lich su ghi 2 lan sang loc");
    }

    @DataProvider(name = "attempts")
    public Object[][] attempts() {
        return new Object[][]{
                // lan sang loc thu n trong ngay, co bi chan khong (bien: duoi gioi han, dung gioi han, vuot gioi han)
                {LIMIT - 1, false},
                {LIMIT, false},
                {LIMIT + 1, true},
        };
    }

    @Test(dataProvider = "attempts",
          description = "K1: toi da 3 lan HIT/ngay cho cung dinh danh; lan thu 4 bi chan va khong duoc ghi lich su")
    public void repeatedHit_dailyLimit(int attempt, boolean expectBlocked) {
        ScreeningPage screening = makerOpensScreening();

        for (int i = 1; i < attempt; i++) {
            screening.open().screen(TYPE, NAME, ID);
            Assert.assertEquals(screening.resultStatus(), "HIT", "Lan " + i);
        }
        screening.open().screen(TYPE, NAME, ID); // lan thu 'attempt'

        ScreeningHistoryPage history = new ScreeningHistoryPage(driver);
        if (expectBlocked) {
            Assert.assertTrue(screening.waitErrorContains("Vượt giới hạn"),
                    "Phai hien thong bao vuot gioi han: " + screening.allErrors());
            Assert.assertFalse(screening.resultVisible(), "Lan bi chan khong co ket qua sang loc");
            Assert.assertEquals(history.open().rowCount(), attempt - 1, "Lan bi chan khong duoc ghi lich su");
        } else {
            Assert.assertEquals(screening.resultStatus(), "HIT", "Lan " + attempt);
            Assert.assertEquals(history.open().rowCount(), attempt, "So lan sang loc da ghi");
        }
    }

    @Test(description = "K1: sang ngay moi thi bo dem ve 0, duoc sang loc lai va van ra HIT")
    public void newDay_resetsDailyCounter() {
        ScreeningPage screening = makerOpensScreening();
        screening.open().screen(TYPE, NAME, ID);
        String openCase = screening.caseCode();
        for (int i = 2; i <= LIMIT; i++) {
            screening.open().screen(TYPE, NAME, ID);
            Assert.assertEquals(screening.resultStatus(), "HIT", "Lan " + i);
        }

        screening.open().screen(TYPE, NAME, ID);
        Assert.assertTrue(screening.waitErrorContains("Vượt giới hạn"), "Ngay 0: lan " + (LIMIT + 1) + " phai bi chan");

        new SimClockPage(driver).setDayOffset(1);

        screening.open().screen(TYPE, NAME, ID);
        Assert.assertEquals(screening.resultStatus(), "HIT", "Ngay +1 van ra HIT");
        Assert.assertEquals(screening.caseCode(), openCase, "Case chua dong van duoc gan lai (K2)");
        Assert.assertEquals(new ScreeningHistoryPage(driver).open().rowCount(), LIMIT + 1,
                "Lich su ghi them 1 lan o ngay moi");
    }

    @Test(description = "Kich ban ba B: hom nay bi tu choi, hom sau den lai van khong tu dong du dieu kien mo CIF")
    public void refusedToday_notAutoEligibleTomorrow() {
        // Ngay 0: Maker sang loc -> HIT -> danh gia Event -> de xuat
        ScreeningPage screening = makerOpensScreening();
        screening.open().screen(TYPE, NAME, ID);
        Assert.assertEquals(screening.resultStatus(), "HIT");
        String firstCase = screening.caseCode();

        CaseDetailPage caseDetail = new CaseDetailPage(driver).open(firstCase);
        int events = caseDetail.eventCount();
        caseDetail.evaluateEvent(1, "Hit đúng", "Dung doi tuong trong Watchlist");
        for (int n = 2; n <= events; n++) {
            caseDetail.evaluateEvent(n, "Hit sai", "Trung ten, khac nguoi");
        }
        caseDetail.clickButton(CaseDetailPage.BTN_PROPOSE);
        Assert.assertTrue(caseDetail.waitSuccessContains("Đề xuất thành công"));

        // Ngay 0: Checker dong Case - Cham dut quan he -> khong du dieu kien mo CIF
        new LoginPage(driver).loginAs(Config.CHECKER);
        caseDetail.open(firstCase);
        caseDetail.setDecisionReason("Hit dung, cham dut quan he").clickButton(CaseDetailPage.BTN_CLOSE_TERMINATE);
        Assert.assertEquals(caseDetail.waitForStatus("Đã đóng - Chấm dứt quan hệ"), "Đã đóng - Chấm dứt quan hệ");
        Assert.assertEquals(caseDetail.cifDecision(), "Không đủ điều kiện mở CIF", "Ngay 0");

        // Ngay +1: khach den lai, Maker sang loc lai
        new SimClockPage(driver).setDayOffset(1);
        new LoginPage(driver).loginAs(Config.MAKER);
        screening.open().screen(TYPE, NAME, ID);

        Assert.assertEquals(screening.resultStatus(), "HIT", "Cung dau vao + cung Watchlist phai cung ket qua");
        Assert.assertNotEquals(screening.caseCode(), firstCase, "Case cu da dong nen phai mo Case moi de xu ly lai");
        Assert.assertEquals(screening.cifDecision(), "Chờ xử lý case",
                "Khong duoc tu dong du dieu kien mo CIF khi chua co quyet dinh moi cua Checker");
        Assert.assertEquals(new ScreeningHistoryPage(driver).open().rowCount(), 2, "Lich su ghi du 2 lan sang loc");
    }

    @DataProvider(name = "sameInputs")
    public Object[][] sameInputs() {
        return new Object[][]{
                // loai KH, ho ten, CCCD, ket qua mong doi, so Event
                {"Cá nhân", "Nguyen Van A", "001234567890", "HIT", 1},
                {"Cá nhân", "Hoang Van Z", "009999999999", "NO-HIT", 0},
        };
    }

    @Test(dataProvider = "sameInputs",
          description = "Cung dau vao, cung Watchlist: ngay 0 va ngay +1 cho cung ket qua sang loc")
    public void sameInput_sameResult_acrossDays(String type, String fullname, String idNumber,
                                                String expectedResult, int expectedEvents) {
        ScreeningPage screening = makerOpensScreening();

        screening.open().screen(type, fullname, idNumber);
        String day0Result = screening.resultStatus();
        int day0Events = screening.matchCount();

        new SimClockPage(driver).setDayOffset(1);

        screening.open().screen(type, fullname, idNumber);
        Assert.assertEquals(screening.resultStatus(), day0Result, "Ket qua ngay +1 phai giong ngay 0");
        Assert.assertEquals(screening.matchCount(), day0Events, "So Event ngay +1 phai giong ngay 0");
        Assert.assertEquals(day0Result, expectedResult, "Ket qua mong doi");
        Assert.assertEquals(day0Events, expectedEvents, "So Event mong doi");
    }
}
