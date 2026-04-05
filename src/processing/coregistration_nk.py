from pathlib import Path
import numpy as np
import xdem
import geoutils as gu


def load_base_and_mask(base_dem_path, mask_vector_path):
    base_dem_path = Path(base_dem_path)
    mask_vector_path = Path(mask_vector_path)

    dem_base = xdem.DEM(base_dem_path)
    mask_vector = gu.Vector(mask_vector_path)
    mask_raster = mask_vector.create_mask(dem_base)

    return dem_base, mask_vector, mask_raster


def amplify_deramp_parameters(deramp_model, factor_giro=-0.1):
    """
    Modifica parámetros internos del modelo Deramp si existen
    en la metadata esperada. Esto es una intervención experimental.
    """
    if "outputs" not in deramp_model.meta:
        return deramp_model

    outputs = deramp_model.meta.get("outputs", {})
    fitorbin = outputs.get("fitorbin", None)

    if fitorbin is None:
        return deramp_model

    for key in ["fit_params", "coefficients", "params"]:
        if key in fitorbin:
            fitorbin[key] = np.array(fitorbin[key]) * factor_giro

    return deramp_model


def coregister_dem_nk_deramp(
    base_dem_path,
    target_dem_path,
    mask_vector_path,
    output_path,
    factor_giro=-0.1,
    poly_order=1,
):
    base_dem_path = Path(base_dem_path)
    target_dem_path = Path(target_dem_path)
    mask_vector_path = Path(mask_vector_path)
    output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    dem_base, _, mask_raster = load_base_and_mask(base_dem_path, mask_vector_path)
    dem_target = xdem.DEM(target_dem_path)

    # 1. Nuth & Kääb
    nk = xdem.coreg.NuthKaab()
    nk.fit(dem_base, dem_target, inlier_mask=mask_raster)
    dem_shifted = nk.apply(dem_target)

    # 2. Deramp
    dr = xdem.coreg.Deramp(poly_order=poly_order)
    dr.fit(dem_base, dem_shifted, inlier_mask=mask_raster)

    # 3. Ajuste experimental
    dr = amplify_deramp_parameters(dr, factor_giro=factor_giro)

    # 4. Aplicación final
    dem_final = dr.apply(dem_shifted)
    dem_final.to_file(output_path)

    return {
        "base_dem_path": str(base_dem_path),
        "target_dem_path": str(target_dem_path),
        "mask_vector_path": str(mask_vector_path),
        "output_path": str(output_path),
        "factor_giro": factor_giro,
        "poly_order": poly_order,
        "status": "ok",
    }