import {ModelBuildDirector} from '../../../builder/ModelBuildDirector';
import {TwilioModelBuilder} from "../../../builder/channels/TwilioModelBuilder";

const builder = new TwilioModelBuilder();
new ModelBuildDirector(builder);

export const TwilioModel = builder.model;
export const TwilioSchema = builder.schema;
