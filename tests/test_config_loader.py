from src.config_loader import get_sites, get_sites_by_country


def test_loads_ar_and_cl_sites():
    sites = get_sites()
    assert "soul_uniform" in sites
    assert sites["soul_uniform"]["country"] == "AR"
    assert "suitmed_cl" in sites
    assert sites["suitmed_cl"]["country"] == "CL"


def test_filter_by_country():
    cl = get_sites_by_country("CL")
    assert all(cfg["country"] == "CL" for cfg in cl.values())
    assert "soul_uniform" not in cl
