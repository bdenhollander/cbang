/******************************************************************************\

          This file is part of the C! library.  A.K.A the cbang library.

                Copyright (c) 2021-2025, Cauldron Development  Oy
                Copyright (c) 2003-2021, Cauldron Development LLC
                               All rights reserved.

         The C! library is free software: you can redistribute it and/or
        modify it under the terms of the GNU Lesser General Public License
       as published by the Free Software Foundation, either version 2.1 of
               the License, or (at your option) any later version.

        The C! library is distributed in the hope that it will be useful,
          but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
                 Lesser General Public License for more details.

         You should have received a copy of the GNU Lesser General Public
                 License along with the C! library.  If not, see
                         <http://www.gnu.org/licenses/>.

        In addition, BSD licensing may be granted on a case by case basis
        by written permission from at least one of the copyright holders.
           You may request written permission by emailing the authors.

                  For information regarding this software email:
                                 Joseph Coffland
                          joseph@cauldrondevelopment.com

\******************************************************************************/

#pragma once

#include "PathResolver.h"
#include "ConsoleModule.h"
#include "StdModule.h"
#include "Impl.h"

#include <cbang/io/InputSource.h>

#include <map>


namespace cb {
  namespace js {
    class Javascript : public PathResolver {
      SmartPointer<Impl> impl;

      StdModule stdMod;
      ConsoleModule consoleMod;

      typedef std::map<std::string, SmartPointer<Module> > modules_t;
      modules_t modules;

      SmartPointer<Value> nativeProps;

    public:
      Javascript(const std::string &implName = std::string(),
                 const cb::SmartPointer<std::ostream> &stream =
                 cb::SmartPointer<std::ostream>::Phony(&std::cout));

      void setStream(const cb::SmartPointer<std::ostream> &stream);

      SmartPointer<js::Factory> getFactory();
      void define(NativeModule &mod);
      void import(const std::string &module,
                  const std::string &as = std::string());
      SmartPointer<js::Value> eval(const InputSource &source);
      void interrupt();
      SmartPointer<js::StackTrace> getStackTrace(unsigned maxFrames);

      std::string stringify(Value &value);

      SmartPointer<Value> require(const std::string &id);

      // Callbacks
      SmartPointer<Value> require(Callback &cb, Value &args);
    };
  }
}
