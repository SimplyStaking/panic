import { newSpecPage } from "@stencil/core/testing";
import { PanicFooter } from "../panic-footer";

describe('panic-footer', () => {
    it('renders', async () => {
        const page = await newSpecPage({
            components: [PanicFooter],
            html: '<panic-footer></panic-footer>',
        });

        const panicHeader = page.body.querySelector('panic-footer');

        expect(panicHeader).toMatchSnapshot();
    });
});
