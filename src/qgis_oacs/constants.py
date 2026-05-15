import dataclasses


@dataclasses.dataclass(frozen=True)
class IconPath:
    main_logo = ":/plugins/qgis_oacs/graph_3.svg"
    search = ":/plugins/qgis_oacs/search.svg"
    system = ":/plugins/qgis_oacs/manufacturing.svg"
    sampling_feature = ":/plugins/qgis_oacs/lab_panel.svg"
    datastream = ":/plugins/qgis_oacs/stream.svg"
    datastream_type_status = ":/plugins/qgis_oacs/circle.svg"
    datastream_type_observation = ":/plugins/qgis_oacs/eye_tracking.svg"
    deployment = ":/plugins/qgis_oacs/deployed_code.svg"
    feature_has_geospatial_location = ":/plugins/qgis_oacs/location_on.svg"
    feature_does_not_have_geospatial_location = ":/plugins/qgis_oacs/table.svg"
    procedure_type_procedure = ":/plugins/qgis_oacs/procedure.svg"
    system_type_sensor = ":/plugins/qgis_oacs/sensors_krx.svg"
    system_type_actuator = ":/plugins/qgis_oacs/stadia_controller.svg"
    system_type_platform = ":/plugins/qgis_oacs/tools_ladder.svg"
    system_type_sampler = ":/plugins/qgis_oacs/labs.svg"
    system_type_system = ":/plugins/qgis_oacs/manufacturing.svg"
    system_asset_type_equipment = ":/plugins/qgis_oacs/manufacturing.svg"
    system_asset_type_human = ":/plugins/qgis_oacs/manufacturing.svg"
    system_asset_type_living_thing = ":/plugins/qgis_oacs/manufacturing.svg"
    system_asset_type_simulation = ":/plugins/qgis_oacs/manufacturing.svg"
    system_asset_type_process = ":/plugins/qgis_oacs/manufacturing.svg"
    system_asset_type_group = ":/plugins/qgis_oacs/manufacturing.svg"
    system_asset_type_other = ":/plugins/qgis_oacs/manufacturing.svg"


# we look for both `rel=<name>` and `rel=ogc-rel:<name>` because of:
#
# https://github.com/opengeospatial/ogcapi-connected-systems/issues/173
#
@dataclasses.dataclass(frozen=True)
class LinkRelation:
    # singular resource links (used in @link inline properties)
    deployment = "deployment"
    feature_of_interest = "featureOfInterest"
    procedure = "procedure"
    sampling_feature = "samplingFeature"
    system = "system"
    # collection / association links (used in the links[] array)
    control_streams = "controlStreams"
    data_streams = "datastreams"
    deployed_systems = "deployedSystems"
    deployments = "deployments"
    features_of_interest = "featuresOfInterest"
    implementing_systems = "implementingSystems"
    observations = "observations"
    parent_deployment = "parentDeployment"
    parent_system = "parentSystem"
    platform = "platform"
    procedures = "procedures"
    sampled_feature = "sampledFeature"
    sample_of = "sampleOf"
    sampling_features = "samplingFeatures"
    sub_deployments = "subdeployments"
    sub_systems = "subsystems"


@dataclasses.dataclass(frozen=True)
class OgcLinkRelation:
    # singular resource links (used in @link inline properties)
    deployment = "ogc-rel:deployment"
    feature_of_interest = "ogc-rel:featureOfInterest"
    procedure = "ogc-rel:procedure"
    sampling_feature = "ogc-rel:samplingFeature"
    system = "ogc-rel:system"
    # collection / association links (used in the links[] array)
    control_streams = "ogc-rel:controlStreams"
    data_streams = "ogc-rel:datastreams"
    deployed_systems = "ogc-rel:deployedSystems"
    deployments = "ogc-rel:deployments"
    features_of_interest = "ogc-rel:featuresOfInterest"
    implementing_systems = "ogc-rel:implementingSystems"
    observations = "ogc-rel:observations"
    parent_deployment = "ogc-rel:parentDeployment"
    parent_system = "ogc-rel:parentSystem"
    platform = "ogc-rel:platform"
    procedures = "ogc-rel:procedures"
    sampled_feature = "ogc-rel:sampledFeature"
    sample_of = "ogc-rel:sampleOf"
    sampling_features = "ogc-rel:samplingFeatures"
    sub_deployments = "ogc-rel:subdeployments"
    sub_systems = "ogc-rel:subsystems"

