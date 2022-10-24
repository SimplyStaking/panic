import {ModelBuildDirector} from '../../../builder/ModelBuildDirector';
import {PagerDutyModelBuilder} from "../../../builder/channels/PagerDutyModelBuilder";

const builder = new PagerDutyModelBuilder();
new ModelBuildDirector(builder);

export const PagerDutyModel = builder.model;
export const PagerDutySchema = builder.schema;
