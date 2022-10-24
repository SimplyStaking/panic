import {ModelBuildDirector} from '../../../builder/ModelBuildDirector';
import {EmailModelBuilder} from "../../../builder/channels/EmailModelBuilder";

const builder = new EmailModelBuilder();
new ModelBuildDirector(builder);

export const EmailModel = builder.model;
export const EmailSchema = builder.schema;
