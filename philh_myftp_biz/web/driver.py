
class Driver:
    """
    Firefox Web Driver
    
    Wrapper for FireFox Selenium Session
    """

    def __init__(self,
        headless: bool = True,
        eager: bool = False,
        timeout: int = 300
    ) -> None:
        from selenium.webdriver import FirefoxOptions, Firefox
        from selenium.webdriver.firefox.options import Options
        from ..process import SysTask, Sleeper
        from ..terminal import Log

        Log.VERB(
            f'Starting Session\n'+ \
            f'{headless=}\n'+ \
            f'{eager=}\n'+ \
            f'{timeout=}'
        )

        options: Options = FirefoxOptions()

        if eager:
            options.page_load_strategy = 'eager'

        if headless:
            options.add_argument("--headless")

        # Start Chrome Session with options
        self._drvr = Firefox(options=options)

        self.Task = SysTask(self._drvr.service.process.pid)

        # Set Timeouts
        self._drvr.command_executor.set_timeout(timeout)
        self._drvr.set_page_load_timeout(time_to_wait=timeout)
        self._drvr.set_script_timeout(time_to_wait=timeout)

    def reload(self) -> None:
        """Reload the Current Page"""
        from ..terminal import Log

        Log.VERB(f'Reloading Page: {self.URL=}')

        self._drvr.refresh()

    def run(self, code:str):
        """Run JavaScript Code on the Current Page"""
        from selenium.common.exceptions import JavascriptException
        from ..terminal import Log

        try:

            response = self._drvr.execute_script(code)

            Log.VERB(
                f'JavaScript Executed\n'+ \
                f'{self.URL=}\n'+ \
                f'{code=}\n'+ \
                f'{response=}'
            )

            return response
        
        except JavascriptException as e:

            raise RuntimeError(e.msg) from None

    def element(self,
        by: Literal['class', 'id', 'xpath', 'name', 'attr'],
        name: str,
        timeout: int = 30
    ) -> list['WebElement']:
        """Get List of Elements by query"""
        from selenium.webdriver.common.by import By
        from ..terminal import Log
        from ..time import Stopwatch

        sw = Stopwatch().start()

        Log.VERB(f"Finding Element: {by=} | {name=}")

        match by.lower():

            case 'class':

                if isinstance(name, list):
                    name = '.'.join(name)

                BY = By.CLASS_NAME

            case 'id':
                BY = By.ID

            case 'xpath':
                BY = By.XPATH

            case 'name':
                BY = By.NAME

            case 'attr':
                name = f"a[{name}']"
                BY = By.CSS_SELECTOR

            case _:
                raise TypeError(f'"{by}" is an invalid method')

        while sw.elapsed < timeout:

            elements: list['WebElement'] = self._drvr.find_elements(by=BY, value=name)

            # If at least 1 element was found
            if len(elements) > 0:

                Log.VERB(f"Found Elements: {elements=}")

                return elements
            
        return []

    def open(self,
        url: str | URL
    ) -> None:
        """Open a url"""
        from selenium.common.exceptions import WebDriverException
        from urllib3.exceptions import ReadTimeoutError
        from ..terminal import Log

        if isinstance(url, URL):
            url = url.url

        Log.VERB(f"Opening Page: {url=}")

        # Switch to the first tab
        handle = self._drvr.window_handles[0]
        self._drvr.switch_to.window(handle)

        # Open the url
        while True:
            try:
                self._drvr.get(url=url)
                return
            except WebDriverException, ReadTimeoutError:
                Log.WARN('Failed to open url', exc_info=True)

    @single_use
    def close(self) -> None:
        """Close the Session"""
        from selenium.common.exceptions import InvalidSessionIdException
        from ..terminal import Log

        Log.VERB('Closing Session')

        try:
            # Exit Session
            self._drvr.quit()
        except InvalidSessionIdException:
            pass

    __del__ = close

    @property
    def HTML(self) -> str | None:
        """HTML of the Current Page"""
        from selenium.common.exceptions import WebDriverException
        
        try:
            return self._drvr.page_source
        except WebDriverException:
            pass
        
    @property
    def URL(self) -> URL | None:
        """URL of the Current Page"""
        from selenium.common.exceptions import WebDriverException

        try:
            return URL(self._drvr.current_url)
        except WebDriverException:
            pass
