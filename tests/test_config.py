import src.config as config


class TestConfig:
    def test_at_least_20_countries(self):
        assert len(config.COUNTRIES) >= 20

    def test_countries_cover_all_regions(self):
        codes = set(config.COUNTRIES)
        regions = {
            "Европа": {"DE", "FR", "GB", "IT", "ES", "SE", "PL", "CZ", "RU", "TR"},
            "Северная Америка": {"US", "CA"},
            "Латинская Америка": {"BR", "MX", "AR", "CL", "CO"},
            "Азия": {"CN", "JP", "IN", "KR", "ID", "SA"},
            "Африка": {"ZA", "NG", "KE", "EG"},
            "Океания": {"AU"},
        }
        for region, codes in regions.items():
            overlap = codes & set(config.COUNTRIES)
            assert overlap, f"Регион {region} не покрыт ни одной страной"

    def test_analysis_period_at_least_30_years(self):
        assert config.YEAR_TO - config.YEAR_FROM >= 30

    def test_variables_include_inequality_and_socioeconomic(self):
        keys = set(config.VARIABLES)
        assert "sptinc_p99p100_992_j" in keys  # топ-1%
        assert "gptinc_p0p100_992_j" in keys  # Джини
        assert "mgdpro_p0p100_999_i" in keys  # ВВП
        assert "npopul_p0p100_992_i" in keys  # население

    def test_variables_have_russian_labels(self):
        for label in config.VARIABLES.values():
            assert isinstance(label, str) and label
