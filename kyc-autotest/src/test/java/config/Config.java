package config;

/** Cau hinh chung. Doi dia chi web bang: -DbaseUrl=http://127.0.0.1:5000 ; chay an trinh duyet: -Dheadless=true */
public final class Config {
    private Config() {}

    public static final String BASE_URL = System.getProperty("baseUrl", "http://127.0.0.1:5000");
    public static final boolean HEADLESS = Boolean.parseBoolean(System.getProperty("headless", "false"));
    public static final int TIMEOUT_SEC = 10;
    public static final String PASSWORD = "123456";
    public static final String MAKER = "maker01";
    public static final String CHECKER = "checker01";
}
