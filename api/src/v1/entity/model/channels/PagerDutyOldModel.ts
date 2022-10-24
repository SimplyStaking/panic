import {ModelBuildDirector} from '../../../builder/ModelBuildDirector';
import { PagerDutyOldModelBuilder }
    from '../../../builder/channels/PagerDutyOldModelBuilder';

const builder = new PagerDutyOldModelBuilder();
new ModelBuildDirector(builder);

export const PagerDutyOldModel = builder.model;
export const PagerDutySchema = builder.schema;
