# platformio-tools

Scripts for PlatformIO framework updates.

## Note on PlatformIO build structure

Each project should specify at least three values:

- platform (chip family, e.g. ststm32 or atmelavr)
- framework (interfacing method to use in code, e.g. arduino-like or mbed)
- board

Platforms refer to framework packages in platform.json via:

- packageRepositories (contains links to package registries that describe where packages could be downloaded from)
- frameworks (refer to framework package and build script)
- packages (versioning requirements for packages)

## Using with MXChip

1. Checkout required tag of [devkit-sdk](./vendor/devkit-sdk).
2. Content of AZ3166 is essentially a framework in terms of PlatformIO.
3. Add framework description in package.json (as needed by PlatformIO), e.g.:
   ```
   {
       "name": "framework-arduinostm32mxchip",
       "description": "Arduino Wiring-based Framework (ST STM32 MXChip Core)",
       "url": "https://microsoft.github.io/azure-iot-developer-kit/",
       "version":"2.0.0"
   }
   ```
4. Pack the `AZ3166/src` directory into archive so that it unpacks into `framework-arduinostm32mxchip`. Per common convention, archive should be named as `framework-arduinostm32mxchip-<package.version>.<ext>`.
5. Host the package somewhere.
6. Update platform registries/add extra into `platform.json` of `ststm32` platform, update package version requirements as necessary.
7. Generate build script out of `platform.txt` in Arduino IDE format provided with devkit-sdk in AZ3166 directory:
   `./generate_pio_build.py ./vendor/devkit-sdk/AZ3166/src/platform.txt script_template.py mxchip.py`
8. Replace `./builder/frameworks/arduino/mxchip.py` in `ststm32` platform by script generated on previous step.
9. Test.

## Testing project build

1. Create project, configure to use `ststm32` as platform, `arduino` as framework and `mxchip_az3166` as board.
2. Provide custom platform ref which contains the overrides describen in previous section by providing git commit ref in platform parameter, e.g.:
   ```
   platform = https://github.com/<my>/platform-ststm32.git
   ```
   (see [https://docs.platformio.org/en/latest/projectconf/section_env_platform.html#platform](PlatformIO docs))
3. Try to build, eh?

## Testing generation script

Unit tests can be invoked with `./generate_pio_build_test.py`
