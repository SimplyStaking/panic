import { EmailOldModelBuilder } 
    from "../../../builder/channels/EmailOldModelBuilder";
import { ModelBuildDirector } from "../../../builder/ModelBuildDirector";

const builder = new EmailOldModelBuilder();
new ModelBuildDirector(builder);

export const EmailOldModel = builder.model;