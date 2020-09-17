import * as Yup from 'yup';

const PeriodicSchema = () => Yup.object().shape({
  periodic: Yup.number()
    .typeError('Periodic alive reminder must be numeric.'),
});

export default PeriodicSchema;
