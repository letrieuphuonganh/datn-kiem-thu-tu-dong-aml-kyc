package tests;

import base.BaseTest;
import config.Config;
import org.testng.Assert;
import org.testng.annotations.DataProvider;
import org.testng.annotations.Test;
import pages.LoginPage;
import pages.ScreeningPage;

/** Script 3 (Sub-luong B): sang loc khach hang - data-driven tren du lieu Watchlist mau. */
public class ScreeningTest extends BaseTest {

    @DataProvider(name = "screeningData")
    public Object[][] screeningData() {
        return new Object[][]{
                // loai KH, ho ten / ten to chuc, CCCD / So DKKD-MST, ket qua mong doi, so Event, quyet dinh mo CIF
                {"Cá nhân", "Hoang Van Z", "009999999999", "NO-HIT", 0, "Đủ điều kiện mở CIF"},
                {"Tổ chức", "Cong ty XYZ", "", "NO-HIT", 0, "Đủ điều kiện mở CIF"},
                {"Cá nhân", "Nguyen Van A", "001234567890", "HIT", 1, "Chờ xử lý case"},
                {"Cá nhân", "NGUYỄN  VĂN A", "", "HIT", 1, "Chờ xử lý case"},          // chuan hoa ten
                {"Cá nhân", "Tran Thi B", "", "HIT", 2, "Chờ xử lý case"},              // trung 2 ban ghi = 2 Event
                {"Tổ chức", "Cong ty ABC", "", "HIT", 1, "Chờ xử lý case"},
                {"Tổ chức", "Cong ty Khac Ten", "0101234567", "HIT", 1, "Chờ xử lý case"},      // trung Số ĐKKD/MST, khac ten
                {"Tổ chức", "Cong ty XYZ", "0999999999", "NO-HIT", 0, "Đủ điều kiện mở CIF"},  // MST khac, ten khac
                {"Cá nhân", "Le Van C", "001111111111", "NO-HIT", 0, "Đủ điều kiện mở CIF"},   // Inactive
                {"Cá nhân", "Pham Van D", "001222222222", "NO-HIT", 0, "Đủ điều kiện mở CIF"}, // Unauthorized
                {"Cá nhân", "Do Van E", "001333333333", "NO-HIT", 0, "Đủ điều kiện mở CIF"},   // Rejected
                {"Cá nhân", "Cong ty ABC", "", "NO-HIT", 0, "Đủ điều kiện mở CIF"},   // khac loai doi tuong
        };
    }

    @Test(dataProvider = "screeningData",
          description = "Sang loc khach hang tra ve dung HIT/NO-HIT, so Event va quyet dinh mo CIF")
    public void screening_returnsExpectedResult(String type, String fullname, String idNumber,
                                                String expectedResult, int expectedEvents,
                                                String expectedCif) {
        new LoginPage(driver).loginAs(Config.MAKER);
        ScreeningPage screening = new ScreeningPage(driver);

        screening.open().screen(type, fullname, idNumber);

        Assert.assertEquals(screening.resultStatus(), expectedResult, "Ket qua sang loc");
        Assert.assertEquals(screening.matchCount(), expectedEvents, "So ban ghi trung khop");
        Assert.assertEquals(screening.cifDecision(), expectedCif, "Quyet dinh mo CIF");
        if (expectedResult.equals("HIT")) {
            Assert.assertFalse(screening.caseCode().isEmpty(), "HIT phai tao Case");
        } else {
            Assert.assertTrue(screening.caseCode().isEmpty(), "NO-HIT khong duoc tao Case");
            Assert.assertEquals(screening.resultMessage(), "Không phát hiện trùng khớp với Watchlist");
        }
    }
}
