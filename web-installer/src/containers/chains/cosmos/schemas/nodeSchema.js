import * as Yup from 'yup';

const NodeSchema = (props) => Yup.object().shape({
  cosmosNodeName: Yup.string()
    .test(
      'unique-node-name',
      'Node name is not unique.',
      (value) => {
        // const { cosmosConfigs } = props;
        // if (cosmosConfigs.length === 0) {
        //   return true;
        // }
        // for (let i = 0; i < cosmosConfigs.length; i += 1) {
        //   if (cosmosConfigs[i].nodes.length === 0) {
        //     return true;
        //   }
        //   for (let j = 0; j < cosmosConfigs[i].nodes.length; j += 1) {
        //     if (cosmosConfigs[i].nodes[j].cosmosNodeName === value) {
        //       return false;
        //     }
        //   }
        // }
        return true;
      },
    )
    .required('Node name is required.'),
});

export default NodeSchema;
