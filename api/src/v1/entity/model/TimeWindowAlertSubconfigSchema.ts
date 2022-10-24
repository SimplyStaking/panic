import {ModelBuildDirector} from '../../builder/ModelBuildDirector';
import {TimeWindowAlertSubconfigModelBuilder} from "../../builder/TimeWindowAlertSubconfigModelBuilder";

const builderSubconfig = new TimeWindowAlertSubconfigModelBuilder();
new ModelBuildDirector(builderSubconfig);

export const TimeWindowAlertSubconfigModel = builderSubconfig.model;
export const TimeWindowAlertSubconfigSchema = builderSubconfig.schema;
