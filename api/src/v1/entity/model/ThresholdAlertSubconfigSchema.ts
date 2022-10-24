import {ModelBuildDirector} from '../../builder/ModelBuildDirector';
import {ThresholdAlertSubconfigModelBuilder} from "../../builder/ThresholdAlertSubconfigModelBuilder";

const builderSubconfig = new ThresholdAlertSubconfigModelBuilder();
new ModelBuildDirector(builderSubconfig);

export const ThresholdAlertSubconfigModel = builderSubconfig.model;
export const ThresholdAlertSubconfigSchema = builderSubconfig.schema;
