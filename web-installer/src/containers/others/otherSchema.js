import * as Yup from 'yup';

const OtherSchema = () => Yup.object().shape({
  periodic: Yup.number()
    .typeError('Periodic alive reminder must be numeric.'),
});

export default OtherSchema;
