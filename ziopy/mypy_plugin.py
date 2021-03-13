import typing
from mypy.nodes import Decorator
from mypy.plugin import FunctionContext, MethodContext, Plugin, Type
import mypy.types as mt


class CustomPlugin(Plugin):
    def _analyze_decorator(self, function_ctx: FunctionContext) -> Type:
        if isinstance(function_ctx.context, Decorator):
            t = function_ctx.context.type
            if isinstance(t, mt.CallableType):
                # Ensure that the "do" argument is present.
                try:
                    idx = t.arg_names.index("do")
                except ValueError:
                    function_ctx.api.fail(
                        "You must supply an argument called 'do'",
                        function_ctx.context
                    )

                # Ensure that the type of the "do" argument is ziopy.zio.ZIOMonad
                a = t.arg_types[idx]
                if not isinstance(a, mt.Instance) or a.type.fullname != 'ziopy.zio.ZIOMonad':
                    function_ctx.api.fail(
                        "The 'do' parameter must be of type ziopy.zio.ZIOMonad",
                        function_ctx.context
                    )
                    return function_ctx.default_return_type

                # Ensure that the return type is ziopy.zio.ZIO
                b = t.ret_type
                if not isinstance(b, mt.Instance) or b.type.fullname != "ziopy.zio.ZIO":
                    function_ctx.api.fail(
                        "The return value must be of type ziopy.zio.ZIO",
                        function_ctx.context
                    )
                    return function_ctx.default_return_type

                # Ensure that the R parameter in `do: ZIOMonad[R, _]` matches
                # the R parameter in the return type `ZIO[R, _, _]`
                if a.args[0] != b.args[0]:
                    function_ctx.api.fail(
                        (
                            "The 'do' parameter's environment (R) type argument must "
                            "match the return type's environment (R) parameter type"
                        ),
                        function_ctx.context
                    )
                    return function_ctx.default_return_type

                # Ensure that the E parameter in `do: ZIOMonad[_, E]` matches
                # the R parameter in the return type `ZIO[_, E, _]`
                if a.args[1] != b.args[1]:
                    function_ctx.api.fail(
                        (
                            "The 'do' parameter's error (E) type argument must match the return "
                            "type's error (E) parameter type"
                        ),
                        function_ctx.context
                    )
                    return function_ctx.default_return_type

                del t.arg_names[idx]
                del t.arg_kinds[idx]
                del t.arg_types[idx]
                return t
        return function_ctx.default_return_type

    def _analyze_method_context_from_callable(self, method_ctx: MethodContext) -> Type:
        if not isinstance(method_ctx.default_return_type, mt.Instance):
            return method_ctx.default_return_type

        function_type = method_ctx.arg_types[0][0]
        if not isinstance(function_type, mt.CallableType):
            return method_ctx.default_return_type

        func_return_type = function_type.ret_type
        method_ctx.default_return_type.args[2] = func_return_type
        return method_ctx.default_return_type

    def _analyze_method_context_to_callable(self, method_ctx: MethodContext) -> Type:
        if not isinstance(method_ctx.default_return_type, mt.CallableType):
            return method_ctx.default_return_type

        if not isinstance(method_ctx.type, mt.Instance):
            return method_ctx.default_return_type

        if not isinstance(method_ctx.type.args[0], mt.Instance):
            return method_ctx.default_return_type

        f_type = method_ctx.type.args[0].args[0]
        if not isinstance(f_type, mt.CallableType):
            return method_ctx.default_return_type

        method_ctx.default_return_type.arg_types = f_type.arg_types
        method_ctx.default_return_type.arg_kinds = f_type.arg_kinds
        method_ctx.default_return_type.arg_names = f_type.arg_names

        return method_ctx.default_return_type

    def get_function_hook(
        self,
        fullname: str
    ) -> typing.Optional[typing.Callable[[FunctionContext], Type]]:
        if fullname == "ziopy.zio.monadic":
            return self._analyze_decorator
        return None

    def get_method_hook(
        self,
        fullname: str
    ) -> typing.Optional[typing.Callable[[MethodContext], Type]]:
        if fullname == "ziopy.zio.ZIO.from_callable":
            return self._analyze_method_context_from_callable
        elif fullname == "ziopy.zio.ZIO.to_callable":
            return self._analyze_method_context_to_callable
        return None


def plugin(version: str) -> typing.Type[CustomPlugin]:
    return CustomPlugin
