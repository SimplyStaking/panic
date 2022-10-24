import {SeverityAlertSubconfigModelBuilder} from '../../builder/SeverityAlertSubconfigModelBuilder';
import {ModelBuildDirector} from '../../builder/ModelBuildDirector';

const builderSubconfig = new SeverityAlertSubconfigModelBuilder();
new ModelBuildDirector(builderSubconfig);

export const SeverityAlertSubconfigModel = builderSubconfig.model;
export const SeverityAlertSubconfigSchema = builderSubconfig.schema;
