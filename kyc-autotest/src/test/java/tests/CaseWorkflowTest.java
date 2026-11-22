package tests;

import base.BaseTest;
import config.Config;
import org.testng.Assert;
import org.testng.annotations.DataProvider;
import org.testng.annotations.Test;
import org.openqa.selenium.By;
import pages.*;

/** Script 4-6 (Sub-luong B): Maker de xuat, Checker xu ly Case, quyet dinh mo CIF, email gia lap, phan quyen. */
public class CaseWorkflowTest extends BaseTest {

    /** Maker sang loc khach hang trung 1 ban ghi (Nguyen Van A) va tra ve ma Case vua tao. */
    private String makerCreatesCase() {
        new LoginPage(driver).loginAs(Config.MAKER);
        ScreeningPage screening = new ScreeningPage(driver).open();
        screening.screen("Cá nhân", "Nguyen Van A", "001234567890");
        Assert.assertEquals(screening.resultStatus(), "HIT");
        return screening.caseCode();
    }

    /** Maker danh gia Event 1 va de xuat Case, roi doi sang Checker. */
    private void makerProposes(String caseCode, String evaluation, String reason) {
        CaseDetailPage caseDetail = new CaseDetailPage(driver).open(caseCode);
        caseDetail.evaluateEvent(1, evaluation, reason);
        caseDetail.clickButton(CaseDetailPage.BTN_PROPOSE);
        Assert.assertTrue(caseDetail.waitSuccessContains("Đề xuất thành công"));
        Assert.assertEquals(caseDetail.waitForStatus("Chờ Checker"), "Chờ Checker");
    }

    @Test(description = "Luong day du: HIT -> Maker danh gia Hit sai -> Checker dong Hit sai -> du dieu kien mo CIF")
    public void falseHit_closedByChecker_cifEligible() {
        String caseCode = makerCreatesCase();
        makerProposes(caseCode, "Hit sai", "Trung ten nhung khac nguoi");

        LoginPage login = new LoginPage(driver);
        login.loginAs(Config.CHECKER);

        // Maker de xuat -> Checker nhan email gia lap
        MailboxPage mailbox = new MailboxPage(driver).open();
        Assert.assertTrue(mailbox.allEmailsText().contains(caseCode));
        Assert.assertTrue(mailbox.allEmailsText().contains("chờ phê duyệt"));

        CaseDetailPage caseDetail = new CaseDetailPage(driver).open(caseCode);
        caseDetail.setDecisionReason("Xac nhan Hit sai").clickButton(CaseDetailPage.BTN_CLOSE_FALSE_HIT);
        Assert.assertEquals(caseDetail.waitForStatus("Đã đóng - Hit sai"), "Đã đóng - Hit sai");
        Assert.assertEquals(caseDetail.cifDecision(), "Đủ điều kiện mở CIF");
    }

    @DataProvider(name = "trueHitDecisions")
    public Object[][] trueHitDecisions() {
        return new Object[][]{
                // nut, trang thai Case, quyet dinh mo CIF, noi dung email gui Maker
                {"terminate", "Đã đóng - Chấm dứt quan hệ", "Không đủ điều kiện mở CIF", "Hit đúng, chấm dứt quan hệ"},
                {"maintain", "Đã đóng - Duy trì có kiểm soát", "Đủ điều kiện mở CIF - có theo dõi", "Hit đúng, duy trì có kiểm soát"},
        };
    }

    @Test(dataProvider = "trueHitDecisions",
          description = "Hit dung: Checker dong Case theo 2 huong xu ly, kiem tra CIF va email cho Maker")
    public void trueHit_closedByChecker(String action, String expectedStatus, String expectedCif,
                                        String expectedMailText) {
        String caseCode = makerCreatesCase();
        makerProposes(caseCode, "Hit đúng", "Dung doi tuong trong Watchlist");

        new LoginPage(driver).loginAs(Config.CHECKER);
        CaseDetailPage caseDetail = new CaseDetailPage(driver).open(caseCode);
        caseDetail.setDecisionReason("Quyet dinh cua Checker");
        caseDetail.clickButton(action.equals("terminate")
                ? CaseDetailPage.BTN_CLOSE_TERMINATE : CaseDetailPage.BTN_CLOSE_MAINTAIN);

        Assert.assertEquals(caseDetail.waitForStatus(expectedStatus), expectedStatus);
        Assert.assertEquals(caseDetail.cifDecision(), expectedCif);

        // Email gia lap gui lai cho Maker
        new LoginPage(driver).loginAs(Config.MAKER);
        String mails = new MailboxPage(driver).open().allEmailsText();
        Assert.assertTrue(mails.contains(caseCode) && mails.contains(expectedMailText),
                "Maker phai nhan email: " + expectedMailText);
    }

    @Test(description = "Checker khong duoc dong 'Hit sai' khi co Event Hit dung")
    public void closeFalseHit_rejected_whenEventIsTrueHit() {
        String caseCode = makerCreatesCase();
        makerProposes(caseCode, "Hit đúng", "Dung doi tuong");

        new LoginPage(driver).loginAs(Config.CHECKER);
        CaseDetailPage caseDetail = new CaseDetailPage(driver).open(caseCode);
        caseDetail.setDecisionReason("Thu dong Hit sai").clickButton(CaseDetailPage.BTN_CLOSE_FALSE_HIT);

        Assert.assertTrue(caseDetail.waitErrorContains("Chỉ được chọn hành động này khi tất cả Event là Hit sai"),
                "Loi hien thi: " + caseDetail.allErrors());
        Assert.assertEquals(caseDetail.status(), "Chờ Checker");
        Assert.assertEquals(caseDetail.cifDecision(), "Chờ xử lý case");
    }

    @Test(description = "Phan quyen theo trang thai: Case 'Cho Maker' chi Maker de xuat duoc; 'Cho Checker' chi Checker dong duoc")
    public void permissions_followCaseStatus() {
        String caseCode = makerCreatesCase();

        // Cho Maker: Maker co nut De xuat, khong co nut dong Case
        CaseDetailPage caseDetail = new CaseDetailPage(driver).open(caseCode);
        Assert.assertEquals(caseDetail.status(), "Chờ Maker");
        Assert.assertTrue(caseDetail.canDo(CaseDetailPage.BTN_PROPOSE));
        Assert.assertFalse(caseDetail.canDo(CaseDetailPage.BTN_CLOSE_FALSE_HIT));

        // Checker chi xem khi Case dang Cho Maker
        new LoginPage(driver).loginAs(Config.CHECKER);
        caseDetail.open(caseCode);
        Assert.assertFalse(caseDetail.canDo(CaseDetailPage.BTN_PROPOSE));
        Assert.assertFalse(caseDetail.canDo(CaseDetailPage.BTN_CLOSE_FALSE_HIT));

        // Sau khi Maker de xuat -> Cho Checker: Maker chi xem, Checker duoc xu ly
        new LoginPage(driver).loginAs(Config.MAKER);
        makerProposes(caseCode, "Hit sai", "Khac nguoi");
        Assert.assertFalse(caseDetail.canDo(CaseDetailPage.BTN_PROPOSE));

        new LoginPage(driver).loginAs(Config.CHECKER);
        caseDetail.open(caseCode);
        Assert.assertTrue(caseDetail.canDo(CaseDetailPage.BTN_CLOSE_FALSE_HIT));
        Assert.assertTrue(caseDetail.canDo(CaseDetailPage.BTN_REQUEST_SUPPLEMENT));
    }
}
