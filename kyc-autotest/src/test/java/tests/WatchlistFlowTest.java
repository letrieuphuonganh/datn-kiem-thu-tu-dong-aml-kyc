package tests;

import base.BaseTest;
import config.Config;
import org.testng.Assert;
import org.testng.annotations.Test;
import pages.*;

/** Script 1 (Sub-luong A): Maker nhap -> Checker Authorize -> Cap nhat Watchlist. */
public class WatchlistFlowTest extends BaseTest {

    @Test(description = "Maker nhap ban ghi, Checker Authorize, cap nhat Watchlist thi ban ghi vao Watchlist")
    public void makerCreates_checkerAuthorizes_watchlistUpdated() {
        LoginPage login = new LoginPage(driver);
        RecordsPage records = new RecordsPage(driver);
        RecordFormPage form = new RecordFormPage(driver);
        RecordDetailPage detail = new RecordDetailPage(driver);
        WatchlistPage watchlist = new WatchlistPage(driver);

        // 1. Maker them moi ban ghi hop le
        login.loginAs(Config.MAKER);
        records.open().clickAdd();
        form.fill("Cá nhân", "Auto Test Nguyen", "001777777777", "1985")
            .fillOptional("Viet Nam", "Du lieu kiem thu tu dong", "Active")
            .save();
        Assert.assertTrue(form.waitSuccessContains("Lưu bản ghi thành công"),
                "Phai co thong bao Luu ban ghi thanh cong");
        String code = form.savedCode();

        // 2. Ban ghi o trang thai Unauthorized va chua vao Watchlist
        detail.open(code);
        Assert.assertEquals(detail.authStatus(), "Unauthorized");
        Assert.assertFalse(detail.inWatchlist(), "Chua duyet thi chua duoc co trong Watchlist");

        // 3. Checker Authorize
        login.loginAs(Config.CHECKER);
        records.open();
        records.selectRecord(code);
        records.authorizeSelected();
        detail.open(code);
        Assert.assertEquals(detail.authStatus(), "Authorized");

        // 4. Checker cap nhat Watchlist
        watchlist.open().update();
        Assert.assertTrue(watchlist.waitSuccessContains("Cập nhật Watchlist thành công"));
        watchlist.open();
        Assert.assertTrue(watchlist.containsRecord(code), "Ban ghi Authorized + Active phai co trong Watchlist");
    }
}
