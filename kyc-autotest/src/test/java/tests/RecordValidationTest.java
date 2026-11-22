package tests;

import base.BaseTest;
import config.Config;
import org.testng.Assert;
import org.testng.annotations.DataProvider;
import org.testng.annotations.Test;
import pages.LoginPage;
import pages.RecordFormPage;
import pages.RecordsPage;

/** Script 2 (Sub-luong A): kiem tra du lieu nhap sai - data-driven (mot script, nhieu bo du lieu). */
public class RecordValidationTest extends BaseTest {

    @DataProvider(name = "invalidRecords")
    public Object[][] invalidRecords() {
        return new Object[][]{
                // loai doi tuong, ho ten / ten to chuc, CCCD / So DKKD-MST, nam sinh, thong bao loi mong doi
                {"Cá nhân", "", "001234567899", "1990", "Họ và tên là bắt buộc"},
                {"Cá nhân", "A".repeat(101), "", "", "Họ và tên không được vượt quá 100 ký tự"},
                {"Cá nhân", "Nguyen Test", "12345678901", "", "Số CCCD phải gồm đúng 12 chữ số"},
                {"Cá nhân", "Nguyen Test", "12345678901A", "", "Số CCCD phải gồm đúng 12 chữ số"},
                {"Cá nhân", "Nguyen Test", "001234567899", "19900", "Năm sinh phải gồm 4 chữ số (YYYY)"},
                {"Cá nhân", "Nguyen Test", "001234567899", "abcd", "Năm sinh phải gồm 4 chữ số (YYYY)"},
                // Tổ chức: nhãn "Tên tổ chức" và "Số ĐKKD/MST" (10 số hoặc 10 số-3 số)
                {"Tổ chức", "", "", "", "Tên tổ chức là bắt buộc"},
                {"Tổ chức", "A".repeat(101), "", "", "Tên tổ chức không được vượt quá 100 ký tự"},
                {"Tổ chức", "Cong ty Test", "123456789", "", "Số ĐKKD/MST phải gồm 10 chữ số hoặc 13 ký tự dạng 10 chữ số-3 chữ số"},
                {"Tổ chức", "Cong ty Test", "001234567890", "", "Số ĐKKD/MST phải gồm 10 chữ số hoặc 13 ký tự dạng 10 chữ số-3 chữ số"},
                {"Tổ chức", "Cong ty Test", "0101234567-01", "", "Số ĐKKD/MST phải gồm 10 chữ số hoặc 13 ký tự dạng 10 chữ số-3 chữ số"},
        };
    }

    @Test(dataProvider = "invalidRecords",
          description = "Nhap sai du lieu thi hien thong bao loi va khong luu ban ghi")
    public void invalidInput_showsErrorAndNotSaved(String type, String fullname, String idNumber,
                                                   String birthYear, String expectedError) {
        new LoginPage(driver).loginAs(Config.MAKER);
        RecordsPage records = new RecordsPage(driver);
        RecordFormPage form = new RecordFormPage(driver);

        records.open().clickAdd();
        form.fill(type, fullname, idNumber, birthYear).save();

        Assert.assertTrue(form.waitErrorContains(expectedError),
                "Mong doi loi: '" + expectedError + "' nhung thuc te: " + form.allErrors());
        Assert.assertFalse(form.hasSuccessMessage(), "Khong duoc hien thong bao thanh cong khi du lieu sai");
    }
}
